from rest_framework import serializers
from .models import (
    UserMovieInteraction, UserGenrePreference, Watchlist,
    Collection, CollectionRule,
)


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
            return f"https://image.tmdb.org/t/p/w500{obj.poster_path}"
        return None


class CollectionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionRule
        fields = ["id", "field", "value"]
        read_only_fields = ["id"]


class CollectionSerializer(serializers.ModelSerializer):
    rules = CollectionRuleSerializer(many=True)
    owner = serializers.CharField(source="user.username", read_only=True)
    movie_count = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = [
            "id", "name", "description", "is_public", "cover_backdrop",
            "cover_url", "owner", "rules", "movie_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def get_movie_count(self, obj):
        return getattr(obj, "_movie_count", None)

    def get_cover_url(self, obj):
        if obj.cover_backdrop:
            return f"{settings.TMDB_IMAGE_BASE_URL}/w1280{obj.cover_backdrop}"
        return None

    def create(self, validated_data):
        rules_data = validated_data.pop("rules", [])
        collection = Collection.objects.create(**validated_data)
        for rule_data in rules_data:
            CollectionRule.objects.create(collection=collection, **rule_data)
        return collection

    def update(self, instance, validated_data):
        rules_data = validated_data.pop("rules", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if rules_data is not None:
            instance.rules.all().delete()
            for rule_data in rules_data:
                CollectionRule.objects.create(collection=instance, **rule_data)

        return instance
