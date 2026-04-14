from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"watchlist", views.WatchlistViewSet, basename="watchlist")
router.register(r"collections", views.CollectionViewSet, basename="collection")

urlpatterns = [
    path("for-you/", views.personalized_recommendations, name="for-you"),
    path("because-you-watched/", views.because_you_watched, name="because-you-watched"),
    path("preferences/", views.genre_preferences, name="genre-preferences"),
    path("track/", views.track_interaction, name="track-interaction"),
    path("dashboard/", views.dashboard_stats, name="dashboard-stats"),
    path("collections/public/", views.public_collections, name="public-collections"),
    path("", include(router.urls)),
]
