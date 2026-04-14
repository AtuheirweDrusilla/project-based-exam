import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Movie, Genre, Person
from .serializers import (
    MovieCompactSerializer, MovieDetailSerializer,
    GenreSerializer, PersonCompactSerializer, PersonDetailSerializer,
    TMDBMovieSerializer,
)
from .services.tmdb_service import TMDBService, MovieSyncService, WikipediaService

logger = logging.getLogger(__name__)
tmdb = TMDBService()
sync_service = MovieSyncService()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MOOD_MAP = {
    "cozy-night": {
        "label": "Cozy Night In",
        "description": "Warm, comforting films perfect for a relaxed evening",
        "genres": "35,10749,16",  # Comedy, Romance, Animation
        "sort_by": "vote_average.desc",
        "vote_count_gte": 200,
        "vote_average_gte": 7.0,
    },
    "adrenaline": {
        "label": "Adrenaline Rush",
        "description": "Heart-pumping action and intense thrills",
        "genres": "28,53,80",  # Action, Thriller, Crime
        "sort_by": "popularity.desc",
        "vote_count_gte": 300,
    },
    "date-night": {
        "label": "Date Night",
        "description": "Romantic and charming films to share with someone special",
        "genres": "10749,35,18",  # Romance, Comedy, Drama
        "sort_by": "vote_average.desc",
        "vote_count_gte": 150,
        "vote_average_gte": 6.5,
    },
    "mind-bender": {
        "label": "Mind Bender",
        "description": "Thought-provoking stories that twist your perception",
        "genres": "878,9648,53",  # Sci-Fi, Mystery, Thriller
        "sort_by": "vote_average.desc",
        "vote_count_gte": 200,
        "vote_average_gte": 7.0,
    },
    "feel-good": {
        "label": "Feel Good",
        "description": "Uplifting stories that leave you smiling",
        "genres": "35,10751,16",  # Comedy, Family, Animation
        "sort_by": "vote_average.desc",
        "vote_count_gte": 150,
        "vote_average_gte": 7.0,
    },
    "edge-of-seat": {
        "label": "Edge of Your Seat",
        "description": "Suspenseful films that keep you guessing",
        "genres": "53,9648,27",  # Thriller, Mystery, Horror
        "sort_by": "popularity.desc",
        "vote_count_gte": 200,
    },
    "epic-adventure": {
        "label": "Epic Adventure",
        "description": "Grand journeys and sweeping tales of heroism",
        "genres": "12,14,878",  # Adventure, Fantasy, Sci-Fi
        "sort_by": "popularity.desc",
        "vote_count_gte": 300,
    },
    "cry-it-out": {
        "label": "Cry It Out",
        "description": "Emotional dramas that hit you right in the feels",
        "genres": "18,10749,10402",  # Drama, Romance, Music
        "sort_by": "vote_average.desc",
        "vote_count_gte": 200,
        "vote_average_gte": 7.5,
    },
    "family-fun": {
        "label": "Family Fun",
        "description": "Movies the whole family can enjoy together",
        "genres": "16,10751,12",  # Animation, Family, Adventure
        "sort_by": "popularity.desc",
        "vote_count_gte": 200,
    },
    "documentary-deep-dive": {
        "label": "Documentary Deep Dive",
        "description": "Real stories that expand your worldview",
        "genres": "99",  # Documentary
        "sort_by": "vote_average.desc",
        "vote_count_gte": 100,
        "vote_average_gte": 7.0,
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize_tmdb_results(tmdb_data, page, include_total=False):
    """Serialize raw TMDB API results into a standard paginated response dict."""
    results = tmdb_data.get("results", [])
    serializer = TMDBMovieSerializer(results, many=True)
    response = {
        "results": serializer.data,
        "total_pages": tmdb_data.get("total_pages", 1),
        "page": page,
    }
    if include_total:
        response["total_results"] = tmdb_data.get("total_results", 0)
    return response


# ---------------------------------------------------------------------------
# ViewSets
# ---------------------------------------------------------------------------

class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    """CRUD-read API for locally-synced movies with TMDB enrichment actions."""

    queryset = Movie.objects.prefetch_related("genres", "directors").all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["genres__slug"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieCompactSerializer

    @action(detail=True, methods=["get"])
    def recommendations(self, request, pk=None):
        """Return TMDB-powered recommendations for a single movie."""
        movie = self.get_object()
        data = tmdb.get_movie_recommendations(movie.tmdb_id)
        results = data.get("results", [])
        serializer = TMDBMovieSerializer(results, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def similar(self, request, pk=None):
        """Return TMDB similar movies for a single movie."""
        movie = self.get_object()
        data = tmdb.get_similar_movies(movie.tmdb_id)
        results = data.get("results", [])
        serializer = TMDBMovieSerializer(results, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def wikipedia(self, request, pk=None):
        """Fetch and persist a Wikipedia summary for a movie."""
        movie = self.get_object()
        year = movie.release_date.year if movie.release_date else None
        wiki_data = WikipediaService.get_movie_summary(movie.title, year)

        if wiki_data.get("summary"):
            movie.wikipedia_summary = wiki_data["summary"]
            movie.wikipedia_url = wiki_data["url"]
            movie.save(update_fields=["wikipedia_summary", "wikipedia_url"])

        return Response(wiki_data)


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    """Genres API."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    @action(detail=True, methods=["get"])
    def movies(self, request, slug=None):
        """GET /api/movies/genres/{slug}/movies/ — movies in this genre."""
        genre = self.get_object()
        page = int(request.query_params.get("page", 1))
        sort = request.query_params.get("sort", "popularity.desc")

        # Prefer local DB when it has enough data to fill a page
        local_movies = Movie.objects.filter(genres=genre).order_by("-popularity")
        if local_movies.count() >= 20:
            paginator = self.paginate_queryset(local_movies)
            serializer = MovieCompactSerializer(paginator, many=True)
            return self.get_paginated_response(serializer.data)

        # Fall back to live TMDB discovery
        data = tmdb.get_movies_by_genre(genre.tmdb_id, page=page, sort_by=sort)
        return Response(_serialize_tmdb_results(data, page, include_total=True))


class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    """People (directors, actors) API."""

    queryset = Person.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PersonDetailSerializer
        return PersonCompactSerializer

    @action(detail=True, methods=["get"])
    def enrich(self, request, pk=None):
        """Fetch extended bio data from TMDB and persist it locally."""
        person = self.get_object()
        data = tmdb.get_person_details(person.tmdb_id)

        if data:
            person.biography = data.get("biography", "")
            person.birthday = data.get("birthday") or None
            person.place_of_birth = data.get("place_of_birth", "")
            person.save()

        serializer = PersonDetailSerializer(person)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Standalone endpoints — search & browse
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([AllowAny])
def search_movies(request):
    """Search movies by title via TMDB."""
    query = request.query_params.get("q", "").strip()
    page = int(request.query_params.get("page", 1))

    if not query:
        return Response(
            {"error": "Query parameter 'q' is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = tmdb.search_movies(query, page=page)
    response = _serialize_tmdb_results(data, page, include_total=True)
    response["query"] = query
    return Response(response)


@api_view(["GET"])
@permission_classes([AllowAny])
def trending_movies(request):
    """Return trending movies for a given time window (day/week)."""
    window = request.query_params.get("window", "week")
    page = int(request.query_params.get("page", 1))

    data = tmdb.get_trending_movies(time_window=window, page=page)
    return Response(_serialize_tmdb_results(data, page))


@api_view(["GET"])
@permission_classes([AllowAny])
def now_playing(request):
    """Return movies currently in theatres."""
    page = int(request.query_params.get("page", 1))
    data = tmdb.get_now_playing(page=page)
    return Response(_serialize_tmdb_results(data, page))


@api_view(["GET"])
@permission_classes([AllowAny])
def top_rated(request):
    """Return highest-rated movies of all time."""
    page = int(request.query_params.get("page", 1))
    data = tmdb.get_top_rated_movies(page=page)
    return Response(_serialize_tmdb_results(data, page))


@api_view(["GET"])
@permission_classes([AllowAny])
def movie_detail_tmdb(request, tmdb_id):
    """Fetch full movie details from TMDB, optionally syncing to local DB."""
    sync = request.query_params.get("sync", "false").lower() == "true"

    if sync:
        movie = sync_service.sync_movie(tmdb_id)
        if movie:
            serializer = MovieDetailSerializer(movie)
            return Response(serializer.data)

    data = tmdb.get_movie_details(tmdb_id)
    if not data:
        return Response({"error": "Movie not found"}, status=404)

    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def search_people(request):
    """Search directors, actors, and crew by name."""
    query = request.query_params.get("q", "").strip()
    if not query:
        return Response({"error": "Query parameter 'q' is required"}, status=400)

    data = tmdb.search_people(query)
    return Response(data)


# ---------------------------------------------------------------------------
# Mood-based discovery
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([AllowAny])
def mood_list(request):
    """Return all available mood categories with labels and descriptions."""
    moods = [
        {"slug": slug, "label": mood["label"], "description": mood["description"]}
        for slug, mood in MOOD_MAP.items()
    ]
    return Response(moods)


@api_view(["GET"])
@permission_classes([AllowAny])
def mood_movies(request, mood_slug):
    """Discover movies matching a mood profile via TMDB genre/rating filters."""
    mood = MOOD_MAP.get(mood_slug)
    if not mood:
        return Response({"error": "Unknown mood"}, status=404)

    page = int(request.query_params.get("page", 1))
    params = {
        "with_genres": mood["genres"],
        "sort_by": mood.get("sort_by", "popularity.desc"),
        "page": page,
    }
    if "vote_count_gte" in mood:
        params["vote_count.gte"] = mood["vote_count_gte"]
    if "vote_average_gte" in mood:
        params["vote_average.gte"] = mood["vote_average_gte"]

    data = tmdb.discover_movies(**params)
    results = data.get("results", [])
    serializer = TMDBMovieSerializer(results, many=True)

    return Response({
        "mood": {"slug": mood_slug, "label": mood["label"], "description": mood["description"]},
        "results": serializer.data,
        "total_pages": data.get("total_pages", 1),
        "page": page,
    })


# ---------------------------------------------------------------------------
# Advanced discover / filters
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([AllowAny])
def discover_filtered(request):
    """Discover movies with flexible query-param filters forwarded to TMDB."""
    params = {}
    page = int(request.query_params.get("page", 1))
    params["page"] = page

    genre = request.query_params.get("genre")
    if genre:
        params["with_genres"] = genre

    year_from = request.query_params.get("year_from")
    year_to = request.query_params.get("year_to")
    if year_from:
        params["primary_release_date.gte"] = f"{year_from}-01-01"
    if year_to:
        params["primary_release_date.lte"] = f"{year_to}-12-31"

    rating_min = request.query_params.get("rating_min")
    if rating_min:
        params["vote_average.gte"] = float(rating_min)
        params["vote_count.gte"] = 50

    runtime_min = request.query_params.get("runtime_min")
    runtime_max = request.query_params.get("runtime_max")
    if runtime_min:
        params["with_runtime.gte"] = int(runtime_min)
    if runtime_max:
        params["with_runtime.lte"] = int(runtime_max)

    language = request.query_params.get("language")
    if language:
        params["with_original_language"] = language

    sort = request.query_params.get("sort", "popularity.desc")
    params["sort_by"] = sort

    data = tmdb.discover_movies(**params)
    return Response(_serialize_tmdb_results(data, page, include_total=True))


# ---------------------------------------------------------------------------
# Movie comparison
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([AllowAny])
def compare_movies(request):
    """Fetch full details for two movies side-by-side. Usage: ?ids=550,680"""
    ids_str = request.query_params.get("ids", "")
    ids = [int(i.strip()) for i in ids_str.split(",") if i.strip().isdigit()]

    if len(ids) < 2:
        return Response({"error": "Provide at least 2 TMDB IDs: ?ids=550,680"}, status=400)

    movies = []
    for movie_id in ids[:2]:
        data = tmdb.get_movie_details(movie_id)
        if data and "id" in data:
            movies.append(data)

    if len(movies) < 2:
        return Response({"error": "Could not fetch both movies"}, status=404)

    return Response({"movies": movies})