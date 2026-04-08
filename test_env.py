import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TMDB_API_KEY")

url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}"

response = requests.get(url)

data = response.json()

print(data["results"][0]["title"])