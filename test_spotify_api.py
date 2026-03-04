import requests
from bs4 import BeautifulSoup
import re
import json

def fetch_spotify_charts():
    """
    Test scraping the official spotify charts site for the Weekly Top Songs 
    """
    print("\n--- Testing Spotify Charts Global Weekly ---")
    url = "https://charts.spotify.com/charts/view/regional-global-weekly/latest"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            print("Successfully fetched charts.spotify.com. Searching for JSON data payload...")
            # Spotify injects initial state into a script tag
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', res.text)
            if match:
                data = json.loads(match.group(1))
                print("Found __NEXT_DATA__ JSON payload.")
                # We will inspect this manual logic in the next step to extract the actual chart entries.
            else:
                print("Could not find __NEXT_DATA__")
        else:
            print(f"Failed to fetch: HTTP {res.status_code}")
    except Exception as e:
        print(f"Error fetching spotify charts: {e}")

fetch_spotify_charts()
