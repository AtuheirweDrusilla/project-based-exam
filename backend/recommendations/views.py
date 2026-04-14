from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import UserMovieInteraction, UserGenrePreference, Watchlist, Collection
from .serializers import (
    UserMovieInteractionSerializer,
    UserGenrePreferenceSerializer,
    WatchlistSerializer,
    CollectionSerializer,
    CollectionCompactSerializer,
)
from .services.engine import RecommendationEngine
from movies.serializers import TMDBMovieSerializer
from movies.services.tmdb_service import TMDBService

engine = RecommendationEngine()
_tmdb = TMDBService()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def personalized_recommendations(request):
    """GET /api/recommendations/for-you/ → personalized picks."""
    page = int(request.query_params.get("page", 1))
    movies = engine.get_recommendations(request.user, page=page)
    serializer = TMDBMovieSerializer(movies, many=True)
    return Response({"results": serializer.data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def because_you_watched(request):
    """GET /api/recommendations/because-you-watched/"""
    data = engine.get_because_you_watched(request.user)
    result = {}
    for title, movies in data.items():
        result[title] = TMDBMovieSerializer(movies, many=True).data
    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def genre_preferences(request):
    """GET /api/recommendations/preferences/"""
    # Recomputing preferences
    engine.compute_genre_preferences(request.user)
    prefs = UserGenrePreference.objects.filter(user=request.user)
    serializer = UserGenrePreferenceSerializer(prefs, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def track_interaction(request):
    """
    POST /api/recommendations/track/
    Body: { movie_tmdb_id, movie_title, interaction_type, genre_ids?, rating? }
    """
    serializer = UserMovieInteractionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WatchlistViewSet(viewsets.ModelViewSet):
    """User's watchlist CRUD."""
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_watched(self, request, pk=None):
        """POST /api/recommendations/watchlist/{id}/mark_watched/"""
        item = self.get_object()
        item.watched = True
        item.watched_at = timezone.now()
        item.save()
        return Response(WatchlistSerializer(item).data)


### dashboard stats

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    GET /api/recommendations/dashboard/
    Returns aggregated stats for the user's dashboard.
    """
    from collections import Counter
    from django.db.models import Count, Avg
    from django.db.models.functions import TruncDate

    user = request.user

    ## all interactions
    interactions = UserMovieInteraction.objects.filter(user=user)
    total_interactions = interactions.count()
    likes = interactions.filter(interaction_type="like").count()
    dislikes = interactions.filter(interaction_type="dislike").count()
    watched = interactions.filter(interaction_type="watched").count()
    searches = interactions.filter(interaction_type="search").count()

    ### watchlist stats
    watchlist = Watchlist.objects.filter(user=user)
    watchlist_total = watchlist.count()
    watchlist_watched = watchlist.filter(watched=True).count()

    ## genre distribution from interactions
    genre_counter = Counter()
    for interaction in interactions.filter(interaction_type__in=["like", "watched", "watchlist"]):
        for gid in interaction.genre_ids:
            genre_counter[gid] += 1

    ## mapping genre IDs to names
    from movies.models import Genre
    genre_distribution = []
    for gid, count in genre_counter.most_common(10):
        try:
            genre = Genre.objects.get(tmdb_id=gid)
            genre_distribution.append({"name": genre.name, "tmdb_id": gid, "count": count})
        except Genre.DoesNotExist:
            genre_distribution.append({"name": f"Genre {gid}", "tmdb_id": gid, "count": count})

    engine.compute_genre_preferences(user)
    prefs = UserGenrePreference.objects.filter(user=user).order_by("-weight")[:10]
    preference_scores = [
        {"name": p.genre_name, "weight": round(p.weight, 1), "count": p.interaction_count}
        for p in prefs
    ]

    ## the activity over time (last 30 days)
    from datetime import timedelta
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_activity = (
        interactions.filter(created_at__gte=thirty_days_ago)
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )
    activity_timeline = [
        {"date": str(d["date"]), "count": d["count"]}
        for d in daily_activity
    ]

    ### recent interactions
    recent = interactions.order_by("-created_at")[:10]
    recent_data = UserMovieInteractionSerializer(recent, many=True).data

    ### average rating given
    avg_rating = interactions.filter(rating__isnull=False).aggregate(avg=Avg("rating"))["avg"]

    return Response({
        "summary": {
            "total_interactions": total_interactions,
            "likes": likes,
            "dislikes": dislikes,
            "watched": watched,
            "searches": searches,
            "watchlist_total": watchlist_total,
            "watchlist_watched": watchlist_watched,
            "average_rating": round(avg_rating, 1) if avg_rating else None,
        },
        "genre_distribution": genre_distribution,
        "preference_scores": preference_scores,
        "activity_timeline": activity_timeline,
        "recent_activity": recent_data,
    })


# ---------------------------------------------------------------------------
# Smart Collections
# ---------------------------------------------------------------------------

def _build_discover_params(rules):
    """Convert a list of CollectionRule instances into TMDB discover kwargs."""
    params: dict = {}
    genres = []
    for rule in rules:
        field, value = rule.field, rule.value
        if field == "genre":
            genres.append(value)
        elif field == "year_min":
            params["primary_release_date.gte"] = f"{value}-01-01"
        elif field == "year_max":
            params["primary_release_date.lte"] = f"{value}-12-31"
        elif field == "rating_min":
            params["vote_average.gte"] = float(value)
            params.setdefault("vote_count.gte", 50)
        elif field == "rating_max":
            params["vote_average.lte"] = float(value)
        elif field == "runtime_min":
            params["with_runtime.gte"] = int(value)
        elif field == "runtime_max":
            params["with_runtime.lte"] = int(value)
        elif field == "language":
            params["with_original_language"] = value
        elif field == "sort_by":
            params["sort_by"] = value
    if genres:
        params["with_genres"] = ",".join(genres)
    params.setdefault("sort_by", "popularity.desc")
    return params


class CollectionViewSet(viewsets.ModelViewSet):
    """CRUD for user-created smart collections with auto-populated movies."""

    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return CollectionCompactSerializer
        return CollectionSerializer

    def get_queryset(self):
        return Collection.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def movies(self, request, pk=None):
        """Return TMDB movies matching this collection's rules."""
        collection = self.get_object()
        page = int(request.query_params.get("page", 1))
        params = _build_discover_params(collection.rules.all())
        params["page"] = page
        data = _tmdb.discover_movies(**params)
        results = data.get("results", [])
        serializer = TMDBMovieSerializer(results, many=True)
        return Response({
            "collection": CollectionCompactSerializer(collection).data,
            "results": serializer.data,
            "total_pages": data.get("total_pages", 1),
            "total_results": data.get("total_results", 0),
            "page": page,
        })

    @action(detail=False, methods=["post"], url_path="preview")
    def preview(self, request):
        """Preview movies for a set of rules without saving a collection."""
        rules_data = request.data.get("rules", [])
        page = int(request.data.get("page", 1))

        class _RuleProxy:
            def __init__(self, d):
                self.field = d.get("field", "")
                self.value = d.get("value", "")

        rule_proxies = [_RuleProxy(r) for r in rules_data]
        params = _build_discover_params(rule_proxies)
        params["page"] = page
        data = _tmdb.discover_movies(**params)
        results = data.get("results", [])
        serializer = TMDBMovieSerializer(results, many=True)
        return Response({
            "results": serializer.data,
            "total_pages": data.get("total_pages", 1),
            "total_results": data.get("total_results", 0),
            "page": page,
        })

    @action(detail=True, methods=["get"], permission_classes=[AllowAny], url_path="public")
    def public_detail(self, request, pk=None):
        """Allow anyone to view a public collection and its movies."""
        try:
            collection = Collection.objects.get(pk=pk, is_public=True)
        except Collection.DoesNotExist:
            return Response({"detail": "Not found or not public."}, status=404)

        page = int(request.query_params.get("page", 1))
        params = _build_discover_params(collection.rules.all())
        params["page"] = page
        data = _tmdb.discover_movies(**params)
        results = data.get("results", [])
        serializer = TMDBMovieSerializer(results, many=True)
        return Response({
            "collection": CollectionSerializer(collection).data,
            "results": serializer.data,
            "total_pages": data.get("total_pages", 1),
            "total_results": data.get("total_results", 0),
            "page": page,
        })


@api_view(["GET"])
@permission_classes([AllowAny])
def public_collections(request):
    """List all public collections from all users."""
    qs = Collection.objects.filter(is_public=True).select_related("user")
    serializer = CollectionCompactSerializer(qs, many=True)
    return Response(serializer.data)
