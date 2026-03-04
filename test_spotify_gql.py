import requests
import os

proxies = {
  "http": "http://127.0.0.1:7890",
  "https": "http://127.0.0.1:7890",
}
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch_spotify_artist_gql(artist_id):
    """
    Test using the unauthenticated Spotify GraphQL endpoint that powers the web player.
    """
    print(f"\n--- Testing Spotify Web Player API ({artist_id}) ---")
    
    # Needs a bearer token from the web player. We can usually get a client token anonymously.
    try:
        # 1. Get anonymous token
        token_res = requests.get("https://open.spotify.com/get_access_token?reason=transport&productType=web_player", headers=headers, proxies=proxies, timeout=10)
        if token_res.status_code != 200:
            print("Failed to get anonymous token")
            return
            
        token = token_res.json().get("accessToken")
        print(f"Got anonymous web token: {token[:10]}...")

        # 2. Query the GraphQL endpoint used by the artist page
        gql_url = "https://api-partner.spotify.com/pathfinder/v1/query"
        gql_headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": headers["User-Agent"]
        }
        
        # Operation: queryArtistOverview
        params = {
            "operationName": "queryArtistOverview",
            "variables": f'{{"uri":"spotify:artist:{artist_id}","locale":"","includePrerelease":false}}',
            "extensions": '{"persistedQuery":{"version":1,"sha256Hash":"3ea563e1d68f486d8df30f51d6edeb0b10629ec23da62547b4d1b3f9ffc12940"}}'
        }
        
        res = requests.get(gql_url, headers=gql_headers, params=params, proxies=proxies, timeout=10)
        data = res.json()
        
        artist_data = data.get("data", {}).get("artistUnion", {})
        stats = artist_data.get("stats", {})
        monthly_listeners = stats.get("monthlyListeners")
        world_rank = stats.get("worldRank")
        
        print(f"Artist: {artist_data.get('profile', {}).get('name')}")
        print(f"Monthly Listeners: {monthly_listeners}")
        print(f"World Rank: {world_rank}")
        
    except Exception as e:
        print(f"Error: {e}")

fetch_spotify_artist_gql("0du5cEVh5yTK9QJze8zA0C") # Bruno Mars
