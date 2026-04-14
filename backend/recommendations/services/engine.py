import logging
from collections import Counter
from django.db.models import Avg, Count
from movies.services.tmdb_service import TMDBService

logger = logging.getLogger(__name__)

# Weights applied to each interaction type when computing genre preferences.
# Positive values boost a genre's score; negative values penalise it.
INTERACTION_WEIGHTS = {
    "like": 5.0,
    "watched": 3.0,
    "watchlist": 2.5,
    "view": 1.0,
    "search": 0.5,
    "dislike": -3.0,
}

DEFAULT_INTERACTION_WEIGHT = 1.0


class RecommendationEngine:
    """Generate personalised movie recommendations from user interaction history."""

    def __init__(self):
        self.tmdb = TMDBService()

    def compute_genre_preferences(self, user) -> list:
        """Score each genre based on the user's interaction history and persist the results."""
        from recommendations.models import UserMovieInteraction, UserGenrePreference
        from movies.models import Genre

        interactions = UserMovieInteraction.objects.filter(user=user)
        genre_scores = Counter()
        genre_names = {}

        for interaction in interactions:
            weight = INTERACTION_WEIGHTS.get(
                interaction.interaction_type, DEFAULT_INTERACTION_WEIGHT
            )
            for genre_id in interaction.genre_ids:
                genre_scores[genre_id] += weight
                if genre_id not in genre_names:
                    try:
                        genre = Genre.objects.get(tmdb_id=genre_id)
                        genre_names[genre_id] = genre.name
                    except Genre.DoesNotExist:
                        genre_names[genre_id] = f"Genre {genre_id}"

        # Normalise scores to a 0–100 range
        if genre_scores:
            max_score = max(genre_scores.values())
            if max_score > 0:
                for genre_id in genre_scores:
                    genre_scores[genre_id] = (genre_scores[genre_id] / max_score) * 100

        # Persist computed preferences
        for genre_id, score in genre_scores.items():
            UserGenrePreference.objects.update_or_create(
                user=user,
                genre_tmdb_id=genre_id,
                defaults={
                    "genre_name": genre_names.get(genre_id, ""),
                    "weight": max(score, 0),
                    "interaction_count": sum(
                        1 for i in interactions if genre_id in i.genre_ids
                    ),
                },
            )

        return sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)

    def get_recommendations(self, user, page: int = 1, limit: int = 20) -> list:
        """Build a ranked list of movie suggestions from the user's top genres."""
        from recommendations.models import UserMovieInteraction

        preferences = self.compute_genre_preferences(user)

        # New users with no history get trending movies as a cold-start fallback
        if not preferences:
            data = self.tmdb.get_trending_movies(page=page)
            return data.get("results", [])

        seen_ids = set(
            UserMovieInteraction.objects.filter(
                user=user,
                interaction_type__in=["watched", "dislike"],
            ).values_list("movie_tmdb_id", flat=True)
        )

        # Fetch candidates from the user's top 3 genres
        top_genres = preferences[:3]
        all_movies = []

        for genre_id, score in top_genres:
            data = self.tmdb.discover_movies(
                with_genres=genre_id,
                sort_by="vote_average.desc",
                vote_count_gte=100,
                page=page,
            )
            movies = data.get("results", [])
            for movie in movies:
                movie["_recommendation_score"] = score * movie.get("vote_average", 0)
            all_movies.extend(movies)

        # De-duplicate and exclude already-seen movies
        seen_in_batch = set()
        unique_movies = []
        for movie in all_movies:
            movie_id = movie["id"]
            if movie_id not in seen_ids and movie_id not in seen_in_batch:
                seen_in_batch.add(movie_id)
                unique_movies.append(movie)

        unique_movies.sort(key=lambda x: x.get("_recommendation_score", 0), reverse=True)
        return unique_movies[:limit]

    def get_director_recommendations(self, director_tmdb_id: int, exclude_movie_id: int = None) -> list:
        """Get other movies by a specific director, sorted by popularity."""
        data = self.tmdb.get_person_details(director_tmdb_id)
        if not data:
            return []

        credits = data.get("movie_credits", {}).get("crew", [])
        directed = [
            credit for credit in credits
            if credit.get("job") == "Director" and credit.get("id") != exclude_movie_id
        ]

        directed.sort(key=lambda x: x.get("popularity", 0), reverse=True)
        return directed[:10]

    def get_because_you_watched(self, user, limit: int = 20) -> dict:
        """Return TMDB recommendations anchored to movies the user recently liked/watched."""
        from recommendations.models import UserMovieInteraction

        recent = UserMovieInteraction.objects.filter(
            user=user,
            interaction_type__in=["watched", "like"],
        ).order_by("-created_at")[:5]

        results = {}
        for interaction in recent:
            data = self.tmdb.get_movie_recommendations(interaction.movie_tmdb_id)
            movies = data.get("results", [])[:5]
            if movies:
                results[interaction.movie_title] = movies

        return results