import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import os
import re

class SpotifyScanner:
    """
    Enhanced Spotify Chart Scraper for Multiple Regions, Types and Artists.
    """
    def __init__(self, region='global', chart_type='daily'):
        # regions: 'global' -> 'ww', 'us' -> 'us'
        # types: 'daily', 'weekly'
        self.region_map = {'global': 'ww', 'us': 'us'}
        self.region_code = self.region_map.get(region, 'ww')
        self.chart_type = chart_type
        
        if chart_type == 'weekly':
            self.base_url = f"https://kworb.net/spotify/country/{self.region_code}_weekly.html"
        else:
            self.base_url = f"https://kworb.net/spotify/country/{self.region_code}_daily.html"
            
        self.db_path = os.path.join(os.path.dirname(__file__), '../../data/polymusic.db')

    def fetch_artists(self):
        """Scrapes the Top Artists chart with robust number parsing."""
        url = "https://kworb.net/spotify/artists.html"
        headers = {"User-Agent": "Mozilla/5.0"}
        print(f"[*] Scraping Top Artists...")
        try:
            res = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            rows = table.find_all('tr')[1:21] # Top 20 artists
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            today = datetime.now().strftime('%Y-%m-%d')
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3: continue
                name = cols[0].text.strip()
                # Use regex to extract only the numeric part, handling things like 50.170 or commas
                stream_text = cols[2].text.strip()
                # Remove everything except digits
                clean_streams = re.sub(r'[^\d]', '', stream_text)
                streams = int(clean_streams) if clean_streams else 0
                
                cursor.execute('''
                    INSERT OR REPLACE INTO spotify_charts (date, region, position, track_name, artist, streams)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (today, 'top_artist', 0, 'ARTIST_ENTRY', name, streams))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Error artist scrape: {e}")

    def fetch_and_save(self):
        """Scrapes tracks with region/type context and robust number parsing."""
        headers = {"User-Agent": "Mozilla/5.0"}
        category = f"{self.region_code}_{self.chart_type}"
        print(f"[*] Scraping {category} charts...")
        try:
            response = requests.get(self.base_url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            if not table: 
                print(f"[!] No table found for {category}")
                return False
            rows = table.find_all('tr')[1:101] # Top 100 for variety
            
            today_str = datetime.now().strftime('%Y-%m-%d')
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 5: continue
                
                pos_text = re.sub(r'[^\d]', '', cols[0].text.strip())
                pos = int(pos_text) if pos_text else 0
                
                full_name = cols[2].text.strip()
                artist, track = full_name.split(" - ", 1) if " - " in full_name else ("Unknown", full_name)
                
                # Robust streams parsing: remove decimals and non-digit characters (like multipliers)
                stream_text = cols[5].text.strip() if len(cols) > 5 else "0"
                # If it's a daily chart, kworb sometimes has '(x4)' etc.
                # We only want the total streams number
                clean_streams = re.sub(r'[^\d]', '', stream_text.split('(')[0]) # Ignore multipliers in parens
                streams = int(clean_streams) if clean_streams else 0

                cursor.execute('''
                    INSERT OR REPLACE INTO spotify_charts (date, region, position, track_name, artist, streams)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (today_str, category, pos, track, artist, streams))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[!] Error scrape {category}: {e}")
            return False

if __name__ == "__main__":
    scanner = SpotifyScanner(region='global')
    scanner.fetch_and_save()
