from datetime import date

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from movies.models import Movie, Genre, Person, WatchProvider
from movies.serializers import TMDBMovieSerializer, _get_release_year
from movies.views import MOOD_MAP


@override_settings(TMDB_IMAGE_BASE_URL="https://image.tmdb.org/t/p")
class MovieModelPropertyTest(TestCase):
    """Movie model computed properties and __str__."""

    def setUp(self):
        self.movie = Movie.objects.create(
            tmdb_id=550,
            title="Fight Club",
            release_date=date(1999, 10, 15),
            poster_path="/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
            backdrop_path="/hZkgoQYus5dXo3H8T7Uef6DNknx.jpg",
            trailer_key="SUXWAEX2jlg",
            vote_average=8.4,
            vote_count=25000,
            popularity=61.0,
        )

    def test_str_includes_title_and_year(self):
        self.assertEqual(str(self.movie), "Fight Club (1999)")

    def test_str_without_release_date(self):
        self.movie.release_date = None
        self.movie.save()
        self.assertEqual(str(self.movie), "Fight Club (N/A)")

    def test_poster_url_builds_full_path(self):
        self.assertEqual(
            self.movie.poster_url,
            "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        )

    def test_poster_url_returns_none_when_empty(self):
        self.movie.poster_path = ""
        self.assertIsNone(self.movie.poster_url)

    def test_poster_url_small_builds_correct_size(self):
        self.assertIn("/w185/", self.movie.poster_url_small)

    def test_backdrop_url_builds_full_path(self):
        self.assertEqual(
            self.movie.backdrop_url,
            "https://image.tmdb.org/t/p/w1280/hZkgoQYus5dXo3H8T7Uef6DNknx.jpg",
        )

    def test_trailer_url(self):
        self.assertEqual(
            self.movie.trailer_url,
            "https://www.youtube.com/watch?v=SUXWAEX2jlg",
        )

    def test_trailer_embed_url(self):
        self.assertEqual(
            self.movie.trailer_embed_url,
            "https://www.youtube.com/embed/SUXWAEX2jlg",
        )

    def test_trailer_url_returns_none_when_empty(self):
        self.movie.trailer_key = ""
        self.assertIsNone(self.movie.trailer_url)


@override_settings(TMDB_IMAGE_BASE_URL="https://image.tmdb.org/t/p")
class PersonModelPropertyTest(TestCase):
    """Person model properties and string representation."""

    def setUp(self):
        self.person = Person.objects.create(
            tmdb_id=7467,
            name="David Fincher",
            profile_path="/tpEczFclQZeKAiCeKZZ0adRvtfz.jpg",
            known_for_department="Directing",
        )

    def test_str(self):
        self.assertEqual(str(self.person), "David Fincher")

    def test_profile_url_builds_full_path(self):
        self.assertEqual(
            self.person.profile_url,
            "https://image.tmdb.org/t/p/w185/tpEczFclQZeKAiCeKZZ0adRvtfz.jpg",
        )

    def test_profile_url_returns_none_when_empty(self):
        self.person.profile_path = ""
        self.assertIsNone(self.person.profile_url)


class GenreModelTest(TestCase):
    """Genre ordering and string representation."""

    def test_str(self):
        genre = Genre.objects.create(tmdb_id=28, name="Action", slug="action")
        self.assertEqual(str(genre), "Action")

    def test_ordering_is_alphabetical(self):
        Genre.objects.create(tmdb_id=878, name="Science Fiction", slug="science-fiction")
        Genre.objects.create(tmdb_id=28, name="Action", slug="action")
        Genre.objects.create(tmdb_id=18, name="Drama", slug="drama")
        names = list(Genre.objects.values_list("name", flat=True))
        self.assertEqual(names, ["Action", "Drama", "Science Fiction"])


@override_settings(TMDB_IMAGE_BASE_URL="https://image.tmdb.org/t/p")
class TMDBMovieSerializerTest(TestCase):
    """TMDBMovieSerializer URL construction and year extraction."""

    SAMPLE_MOVIE = {
        "id": 550,
        "title": "Fight Club",
        "overview": "A depressed man suffering from insomnia...",
        "release_date": "1999-10-15",
        "vote_average": 8.4,
        "vote_count": 25000,
        "popularity": 61.0,
        "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        "backdrop_path": "/hZkgoQYus5dXo3H8T7Uef6DNknx.jpg",
        "genre_ids": [18, 53, 35],
    }

    def test_adds_poster_and_backdrop_urls(self):
        data = TMDBMovieSerializer(self.SAMPLE_MOVIE).data
        self.assertEqual(
            data["poster_url"],
            "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        )
        self.assertEqual(
            data["backdrop_url"],
            "https://image.tmdb.org/t/p/w1280/hZkgoQYus5dXo3H8T7Uef6DNknx.jpg",
        )

    def test_extracts_year_from_release_date(self):
        data = TMDBMovieSerializer(self.SAMPLE_MOVIE).data
        self.assertEqual(data["year"], 1999)

    def test_year_is_none_for_empty_release_date(self):
        raw = {**self.SAMPLE_MOVIE, "release_date": ""}
        data = TMDBMovieSerializer(raw).data
        self.assertIsNone(data["year"])

    def test_no_poster_url_when_path_is_null(self):
        raw = {**self.SAMPLE_MOVIE, "poster_path": None, "backdrop_path": None}
        data = TMDBMovieSerializer(raw).data
        self.assertNotIn("poster_url", data)
        self.assertNotIn("backdrop_url", data)


class SearchEndpointTest(TestCase):
    """search_movies endpoint input validation (no TMDB call needed)."""

    def setUp(self):
        self.client = APIClient()

    def test_missing_query_returns_400(self):
        response = self.client.get("/api/movies/search/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_empty_query_returns_400(self):
        response = self.client.get("/api/movies/search/?q=")
        self.assertEqual(response.status_code, 400)

    def test_whitespace_only_query_returns_400(self):
        response = self.client.get("/api/movies/search/?q=   ")
        self.assertEqual(response.status_code, 400)


class MoodEndpointTest(TestCase):
    """Mood list and mood detail endpoint behaviour."""

    def setUp(self):
        self.client = APIClient()

    def test_mood_list_returns_all_moods(self):
        response = self.client.get("/api/movies/moods/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), len(MOOD_MAP))
        returned_slugs = {m["slug"] for m in data}
        self.assertEqual(returned_slugs, set(MOOD_MAP.keys()))

    def test_mood_list_contains_label_and_description(self):
        response = self.client.get("/api/movies/moods/")
        for mood in response.json():
            self.assertIn("label", mood)
            self.assertIn("description", mood)

    def test_unknown_mood_slug_returns_404(self):
        response = self.client.get("/api/movies/moods/nonexistent-mood/")
        self.assertEqual(response.status_code, 404)


class CompareEndpointTest(TestCase):
    """compare_movies endpoint input validation."""

    def setUp(self):
        self.client = APIClient()

    def test_missing_ids_returns_400(self):
        response = self.client.get("/api/movies/compare/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_single_id_returns_400(self):
        response = self.client.get("/api/movies/compare/?ids=550")
        self.assertEqual(response.status_code, 400)

    def test_non_numeric_ids_returns_400(self):
        response = self.client.get("/api/movies/compare/?ids=abc,def")
        self.assertEqual(response.status_code, 400)


class ReleaseYearHelperTest(TestCase):
    """_get_release_year shared serializer helper."""

    def test_returns_year_when_date_present(self):
        movie = Movie(release_date=date(2023, 7, 21))
        self.assertEqual(_get_release_year(movie), 2023)

    def test_returns_none_when_date_missing(self):
        movie = Movie(release_date=None)
        self.assertIsNone(_get_release_year(movie))


@override_settings(TMDB_IMAGE_BASE_URL="https://image.tmdb.org/t/p")
class MovieListEndpointTest(TestCase):
    """MovieViewSet list endpoint returns local movies and supports filtering."""

    def setUp(self):
        self.client = APIClient()
        self.genre = Genre.objects.create(tmdb_id=28, name="Action", slug="action")
        self.movie = Movie.objects.create(
            tmdb_id=550,
            title="Fight Club",
            release_date=date(1999, 10, 15),
            vote_average=8.4,
            popularity=61.0,
        )
        self.movie.genres.add(self.genre)

    def test_list_returns_movies(self):
        response = self.client.get("/api/movies/list/")
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Fight Club")

    def test_genre_filter_matches(self):
        response = self.client.get("/api/movies/list/?genres__slug=action")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)

    def test_genre_filter_excludes_non_matching(self):
        response = self.client.get("/api/movies/list/?genres__slug=comedy")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 0)


@override_settings(TMDB_IMAGE_BASE_URL="https://image.tmdb.org/t/p")
class WatchProviderModelTest(TestCase):
    """WatchProvider model string representation and logo_url property."""

    def setUp(self):
        self.movie = Movie.objects.create(
            tmdb_id=550, title="Fight Club", popularity=61.0,
        )
        self.provider = WatchProvider.objects.create(
            movie=self.movie,
            provider_name="Netflix",
            provider_type="stream",
            logo_path="/9A1JSVmSxsyaBK4SUFsE887Pjfk.jpg",
        )

    def test_str(self):
        self.assertEqual(str(self.provider), "Netflix (stream) - Fight Club")

    def test_logo_url(self):
        self.assertEqual(
            self.provider.logo_url,
            "https://image.tmdb.org/t/p/w92/9A1JSVmSxsyaBK4SUFsE887Pjfk.jpg",
        )

    def test_logo_url_none_when_empty(self):
        self.provider.logo_path = ""
        self.assertIsNone(self.provider.logo_url)
