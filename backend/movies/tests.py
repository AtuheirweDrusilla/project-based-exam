from datetime import date

from django.test import TestCase, override_settings

from movies.models import Movie


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