from rest_framework import serializers
from .models import Genre, Person, Movie, MovieCast, WatchProvider


class GenreSerializer(serializers.ModelSerializer):
    movie_count = serializers.SerializerMethodField()

    class Meta:
        model = Genre
        fields = ["id", "tmdb_id", "name", "slug", "movie_count"]

    def get_movie_count(self, obj):
        return obj.movies.count()


class PersonCompactSerializer(serializers.ModelSerializer):
    profile_url = serializers.ReadOnlyField()

    class Meta:
        model = Person
        fields = ["id", "tmdb_id", "name", "profile_url", "known_for_department"]
        
    def _get_release_year(obj):
        """Extract the release year from a model instance (shared by compact/detail serializers)."""
        return obj.release_date.year if obj.release_date else None


class PersonDetailSerializer(serializers.ModelSerializer):
    profile_url = serializers.ReadOnlyField()
    directed_movies = serializers.SerializerMethodField()
    acted_movies = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = [
            "id", "tmdb_id", "name", "profile_url", "biography",
            "birthday", "place_of_birth", "known_for_department",
            "directed_movies", "acted_movies",
        ]

    def get_directed_movies(self, obj):
        movies = obj.directed_movies.order_by("-release_date")[:20]
        return MovieCompactSerializer(movies, many=True).data

    def get_acted_movies(self, obj):
        movies = obj.acted_movies.order_by("-release_date")[:20]
        return MovieCompactSerializer(movies, many=True).data


class MovieCastSerializer(serializers.ModelSerializer):
    person = PersonCompactSerializer()

    class Meta:
        model = MovieCast
        fields = ["person", "character", "order"]


class WatchProviderSerializer(serializers.ModelSerializer):
    logo_url = serializers.ReadOnlyField()

    class Meta:
        model = WatchProvider
        fields = ["provider_name", "provider_type", "logo_url", "link"]


class MovieCompactSerializer(serializers.ModelSerializer):
    """Lightweight movie serializer for lists."""
    poster_url = serializers.ReadOnlyField()
    poster_url_small = serializers.ReadOnlyField()
    genres = GenreSerializer(many=True, read_only=True)
    year = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            "id", "tmdb_id", "title", "overview", "release_date", "year",
            "vote_average", "vote_count", "popularity", "poster_url",
            "poster_url_small", "genres", "runtime",
        ]

    def get_year(self, obj):
        return _get_release_year(obj)


class MovieDetailSerializer(serializers.ModelSerializer):
    """Full movie serializer with all relationships."""
    poster_url = serializers.ReadOnlyField()
    backdrop_url = serializers.ReadOnlyField()
    trailer_url = serializers.ReadOnlyField()
    trailer_embed_url = serializers.ReadOnlyField()
    genres = GenreSerializer(many=True, read_only=True)
    directors = PersonCompactSerializer(many=True, read_only=True)
    cast = serializers.SerializerMethodField()
    watch_providers = WatchProviderSerializer(many=True, read_only=True)
    year = serializers.SerializerMethodField()
    wikipedia_url = serializers.ReadOnlyField()
    wikipedia_summary = serializers.ReadOnlyField()

    class Meta:
        model = Movie
        fields = [
            "id", "tmdb_id", "imdb_id", "title", "original_title",
            "overview", "tagline", "release_date", "year", "runtime",
            "vote_average", "vote_count", "popularity",
            "poster_url", "backdrop_url",
            "trailer_url", "trailer_embed_url", "trailer_key",
            "budget", "revenue", "status", "homepage",
            "genres", "directors", "cast", "watch_providers",
            "wikipedia_url", "wikipedia_summary",
        ]

    def get_cast(self, obj):
        cast = MovieCast.objects.filter(movie=obj).select_related("person")[:10]
        return MovieCastSerializer(cast, many=True).data

    def get_year(self, obj):
        return _get_release_year(obj)


class TMDBMovieSerializer(serializers.Serializer):
    """Serializer for raw TMDB API responses (not from DB)."""
    id = serializers.IntegerField()
    title = serializers.CharField()
    overview = serializers.CharField(allow_blank=True)
    release_date = serializers.CharField(allow_blank=True)
    vote_average = serializers.FloatField()
    vote_count = serializers.IntegerField()
    popularity = serializers.FloatField()
    poster_path = serializers.CharField(allow_blank=True, allow_null=True)
    backdrop_path = serializers.CharField(allow_blank=True, allow_null=True)
    genre_ids = serializers.ListField(child=serializers.IntegerField())

    def to_representation(self, instance):
        data = super().to_representation(instance)
        from django.conf import settings
# ... inside method:
        image_base = settings.TMDB_IMAGE_BASE_URL

        if data.get("poster_path"):
            data["poster_url"] = f"{base}/w500{data['poster_path']}"
            data["poster_url_small"] = f"{base}/w185{data['poster_path']}"
        if data.get("backdrop_path"):
            data["backdrop_url"] = f"{base}/w1280{data['backdrop_path']}"
        release_date = data.get("release_date", "")
        data["year"] = int(release_date[:4]) if release_date and len(release_date) >= 4 else None
        return data
