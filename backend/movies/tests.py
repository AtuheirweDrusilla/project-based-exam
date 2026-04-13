from datetime import date
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from movies.models import Movie, Person, WatchProvider, Genre
from movies.serializers import TMDBMovieSerializer
from movies.views import MOOD_MAP


@override_settings(TMDB_IMAGE_BASE_URL="https://image.tmdb.org/t/p")
class MovieModelPropertyTest(TestCase):
    def setUp(self):
        self.movie = Movie.objects.create(
            tmdb_id=550,
            title="Sample Movie",
            release_date=date(1999, 10, 15),
            poster_path="/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
            backdrop_path="/hZkgoQYus5dXo3H8T7Uef6DNknx.jpg",
            trailer_key="SUXWAEX2jlg",
            vote_average=8.4,
            vote_count=25000,
            popularity=61.0,
        )

    def test_string_representation_includes_title_and_year(self):
        self.assertEqual(str(self.movie), "Sample Movie (1999)")

    def test_string_representation_shows_na_when_release_date_is_missing(self):
        self.movie.release_date = None
        self.movie.save()
        self.assertEqual(str(self.movie), "Sample Movie (N/A)")

    def test_poster_url_builds_full_image_path(self):
        self.assertEqual(
            self.movie.poster_url,
            "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        )

    def test_poster_url_returns_none_when_poster_path_is_blank(self):
        self.movie.poster_path = ""
        self.assertIsNone(self.movie.poster_url)

    def test_small_poster_url_uses_w185_size(self):
        self.assertIn("/w185/", self.movie.poster_url_small)

    def test_backdrop_url_builds_full_image_path(self):
        self.assertEqual(
            self.movie.backdrop_url,
            "https://image.tmdb.org/t/p/w1280/hZkgoQYus5dXo3H8T7Uef6DNknx.jpg",
        )

    def test_trailer_url_builds_youtube_watch_link(self):
        self.assertEqual(
            self.movie.trailer_url,
            "https://www.youtube.com/watch?v=SUXWAEX2jlg",
        )

    def test_trailer_embed_url_builds_youtube_embed_link(self):
        self.assertEqual(
            self.movie.trailer_embed_url,
            "https://www.youtube.com/embed/SUXWAEX2jlg",
        )

    def test_trailer_url_returns_none_when_trailer_key_is_blank(self):
        self.movie.trailer_key = ""
        self.assertIsNone(self.movie.trailer_url)

@override_settings(TMDB_IMAGE_BASE_URL="https://image.tmdb.org/t/p")
class PersonModelPropertyTest(TestCase):
    def setUp(self):
        self.person = Person.objects.create(
            tmdb_id=101,
            name="Sample Actor",
            profile_path="/sample-profile.jpg",
            known_for_department="Acting",
        )

    def test_string_representation_returns_name(self):
        self.assertEqual(str(self.person), "Sample Actor")

    def test_profile_url_builds_full_image_path(self):
        self.assertEqual(
            self.person.profile_url,
            "https://image.tmdb.org/t/p/w185/sample-profile.jpg",
        )

    def test_profile_url_returns_none_when_profile_path_is_blank(self):
        self.person.profile_path = ""
        self.assertIsNone(self.person.profile_url)


@override_settings(TMDB_IMAGE_BASE_URL="https://image.tmdb.org/t/p")
class WatchProviderModelPropertyTest(TestCase):
    def setUp(self):
        self.movie = Movie.objects.create(
            tmdb_id=999,
            title="Provider Test Movie",
            vote_average=7.5,
            vote_count=100,
            popularity=50.0,
        )
        self.provider = WatchProvider.objects.create(
            movie=self.movie,
            provider_name="Netflix",
            provider_type="flatrate",
            logo_path="/netflix-logo.jpg",
            link="https://www.netflix.com",
            country_code="US",
        )

    def test_string_representation_includes_provider_name_and_type(self):
        self.assertIn("Netflix", str(self.provider))

    def test_logo_url_builds_full_image_path(self):
        self.assertEqual(
            self.provider.logo_url,
            "https://image.tmdb.org/t/p/w92/netflix-logo.jpg",
        )

    def test_logo_url_returns_none_when_logo_path_is_blank(self):
        self.provider.logo_path = ""
        self.assertIsNone(self.provider.logo_url)

class TMDBMovieSerializerTest(TestCase):
    def test_serializer_builds_image_urls_and_year(self):
        movie_data = {
            "id": 550,
            "title": "Sample Movie",
            "overview": "A sample overview.",
            "release_date": "1999-10-15",
            "vote_average": 8.4,
            "vote_count": 25000,
            "popularity": 61.0,
            "poster_path": "/poster.jpg",
            "backdrop_path": "/backdrop.jpg",
            "genre_ids": [18],
        }

        serializer = TMDBMovieSerializer(instance=movie_data)
        serialized_data = serializer.data

        self.assertEqual(serialized_data["year"], 1999)
        self.assertEqual(
            serialized_data["poster_url"],
            "https://image.tmdb.org/t/p/w500/poster.jpg",
        )
        self.assertEqual(
            serialized_data["poster_url_small"],
            "https://image.tmdb.org/t/p/w185/poster.jpg",
        )
        self.assertEqual(
            serialized_data["backdrop_url"],
            "https://image.tmdb.org/t/p/w1280/backdrop.jpg",
        )

    def test_serializer_handles_blank_release_date(self):
        movie_data = {
            "id": 551,
            "title": "No Date Movie",
            "overview": "Another sample overview.",
            "release_date": "",
            "vote_average": 7.0,
            "vote_count": 500,
            "popularity": 40.0,
            "poster_path": "/poster2.jpg",
            "backdrop_path": "/backdrop2.jpg",
            "genre_ids": [35],
        }

        serializer = TMDBMovieSerializer(instance=movie_data)
        serialized_data = serializer.data

        self.assertIsNone(serialized_data["year"])

    def test_serializer_omits_image_urls_when_paths_are_missing(self):
        movie_data = {
            "id": 552,
            "title": "Missing Images Movie",
            "overview": "Movie without image paths.",
            "release_date": "2005-06-01",
            "vote_average": 6.5,
            "vote_count": 120,
            "popularity": 15.0,
            "poster_path": "",
            "backdrop_path": "",
            "genre_ids": [12],
        }

        serializer = TMDBMovieSerializer(instance=movie_data)
        serialized_data = serializer.data

        self.assertEqual(serialized_data["year"], 2005)
        self.assertNotIn("poster_url", serialized_data)
        self.assertNotIn("poster_url_small", serialized_data)
        self.assertNotIn("backdrop_url", serialized_data)

class SearchEndpointTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_blank_query_returns_400(self):
        response = self.client.post("/api/movies/search/?q=   ")
        self.assertEqual(response.status_code, 400)


class MoodEndpointTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_mood_list_returns_all_moods(self):
        response = self.client.get("/api/movies/moods/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), len(MOOD_MAP))

    def test_each_mood_contains_label_and_description(self):
        response = self.client.get("/api/movies/moods/")
        self.assertEqual(response.status_code, 200)

        for mood in response.json():
            self.assertIn("label", mood)
            self.assertIn("description", mood)

    def test_unknown_mood_slug_returns_404(self):
        response = self.client.get("/api/movies/moods/not-a-real-mood/")
        self.assertEqual(response.status_code, 404)


class CompareEndpointTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_missing_ids_returns_400(self):
        response = self.client.get("/api/movies/compare/")
        self.assertEqual(response.status_code, 400)

    def test_single_id_returns_400(self):
        response = self.client.get("/api/movies/compare/?ids=550")
        self.assertEqual(response.status_code, 400)

    def test_non_numeric_ids_returns_400(self):
        response = self.client.get("/api/movies/compare/?ids=abc,xyz")
        self.assertEqual(response.status_code, 400)

@override_settings(TMDB_IMAGE_BASE_URL="https://image.tmdb.org/t/p")
class MovieListEndpointTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.action_genre = Genre.objects.create(
            tmdb_id=28,
            name="Action",
            slug="action",
        )
        self.comedy_genre = Genre.objects.create(
            tmdb_id=35,
            name="Comedy",
            slug="comedy",
        )

        self.action_movie = Movie.objects.create(
            tmdb_id=700,
            title="Action Movie",
            release_date=date(2020, 1, 1),
            vote_average=8.0,
            vote_count=1000,
            popularity=90.0,
            poster_path="/action.jpg",
        )
        self.action_movie.genres.add(self.action_genre)

        self.comedy_movie = Movie.objects.create(
            tmdb_id=701,
            title="Comedy Movie",
            release_date=date(2021, 1, 1),
            vote_average=7.0,
            vote_count=500,
            popularity=70.0,
            poster_path="/comedy.jpg",
        )
        self.comedy_movie.genres.add(self.comedy_genre)

    def test_list_endpoint_returns_local_movies(self):
        response = self.client.get("/api/movies/list/")
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertIn("results", response_data)
        self.assertEqual(len(response_data["results"]), 2)

    def test_list_endpoint_filters_by_action_genre_slug(self):
        response = self.client.get("/api/movies/list/?genres__slug=action")
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(len(response_data["results"]), 1)
        self.assertEqual(response_data["results"][0]["title"], "Action Movie")

    def test_list_endpoint_excludes_non_matching_genre(self):
        response = self.client.get("/api/movies/list/?genres__slug=horror")
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertEqual(len(response_data["results"]), 0)