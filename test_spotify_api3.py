import requests

# Test Spotify API directly using the client credentials we have in .env
from dotenv import load_dotenv
import os
import base64

load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

if not client_id or not client_secret:
    print("SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not found in .env")
    exit(1)

def get_token():
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = requests.post(url, headers=headers, data=data)
    json_result = result.json()
    token = json_result.get("access_token")
    return token

token = get_token()
print(f"Got Token: {token[:10]}...")

def get_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = {"Authorization": f"Bearer {token}"}
    result = requests.get(url, headers=headers)
    json_result = result.json()
    print("\n--- Artist Data ---")
    print(f"Name: {json_result.get('name')}")
    print(f"Followers: {json_result.get('followers', {}).get('total')}")
    print(f"Popularity: {json_result.get('popularity')}")
    # Note: Monthly Listeners is NOT exposed in the official Spotify Web API /v1/artists/{id} endpoint
    print("Note: Monthly listeners is NOT in the official API response.")

get_artist(token, "0du5cEVh5yTK9QJze8zA0C") # Bruno Mars
