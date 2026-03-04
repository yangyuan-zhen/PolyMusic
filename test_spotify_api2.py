import requests
import json
import os

# Set up proxies for Clash Verge (common local ports on Windows)
proxies = {
  "http": "http://127.0.0.1:7890",
  "https": "http://127.0.0.1:7890",
}
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}

def fetch_spotify_artist_page(artist_id):
    """
    Test scraping the Spotify artist page directly to see if it exposes Monthly Listeners 
    in the __NEXT_DATA__ or similar script blocks.
    """
    print(f"\n--- Testing Spotify Artist Page ({artist_id}) ---")
    url = f"https://open.spotify.com/artist/{artist_id}"
    try:
        res = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        if res.status_code == 200:
            print(f"Successfully fetched {url}.")
            # Look for monthly listeners string
            import re
            match = re.search(r'([\d,]+)\s+monthly listeners', res.text, re.IGNORECASE)
            if match:
                print(f"Found monthly listeners: {match.group(1)}")
            else:
                print("Could not find 'monthly listeners' text in HTML.")
        else:
            print(f"Failed: HTTP {res.status_code}")
    except Exception as e:
        print(f"Error fetching: {e}")

# Bruno Mars ID: 0du5cEVh5yTK9QJze8zA0C
fetch_spotify_artist_page("0du5cEVh5yTK9QJze8zA0C")
