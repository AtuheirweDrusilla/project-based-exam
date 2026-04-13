from rest_framework import serializers
from .models import UserMovieInteraction, UserGenrePreference, Watchlist


class UserMovieInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMovieInteraction
        fields = [
            "id", "movie_tmdb_id", "movie_title", "interaction_type",
            "genre_ids", "rating", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class UserGenrePreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGenrePreference
        fields = ["genre_tmdb_id", "genre_name", "weight", "interaction_count", "updated_at"]


class WatchlistSerializer(serializers.ModelSerializer):
    poster_url = serializers.SerializerMethodField()

    class Meta:
        model = Watchlist
        fields = [
            "id", "movie_tmdb_id", "movie_title", "poster_path",
            "poster_url", "added_at", "watched", "watched_at",
        ]
        read_only_fields = ["id", "added_at"]

    def get_poster_url(self, obj):
        if obj.poster_path:
           from django.conf import settings
# ... inside method:
        return f"{settings.TMDB_IMAGE_BASE_URL}/w500{obj.poster_path}"
        return None
