import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import os
import re

class SpotifyScanner:
    """
    Spotify Top 200 Chart Scraper focusing on kworb.net for high-speed, non-blocked access.
    """
    def __init__(self, region='global'):
        # kworb regions: 'ww' (global), 'us', 'gb', etc.
        self.region_map = {'global': 'ww', 'us': 'us', 'uk': 'gb'}
        self.region_code = self.region_map.get(region, 'ww')
        self.base_url = f"https://kworb.net/spotify/country/{self.region_code}_daily.html"
        self.db_path = os.path.join(os.path.dirname(__file__), '../../data/polymusic.db')

    def fetch_and_save(self):
        """
        Scrapes kworb.net and saves the data to the local SQLite database.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        print(f"[*] Scraping Spotify {self.region_code} charts from kworb...")
        try:
            response = requests.get(self.base_url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Kworb table structure: the main data table
            table = soup.find('table', {'class': 'sortable'})
            if not table:
                print("[!] Could not find the chart table.")
                return False

            rows = table.find_all('tr')[1:201] # Get top 200
            
            today_str = datetime.now().strftime('%Y-%m-%d')
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            count = 0
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 5: continue
                
                pos = int(cols[0].text.strip())
                # Artist - Track format
                full_name = cols[2].text.strip()
                if " - " in full_name:
                    artist, track = full_name.split(" - ", 1)
                else:
                    artist, track = "Unknown", full_name
                
                # Streams often contain commas
                streams_text = cols[5].text.strip().replace(',', '')
                try:
                    streams = int(streams_text)
                except ValueError:
                    streams = 0

                # Insert into DB
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO spotify_charts (date, region, position, track_name, artist, streams)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (today_str, self.region_code, pos, track, artist, streams))
                    count += 1
                except Exception as e:
                    print(f"Error inserting row: {e}")

            conn.commit()
            conn.close()
            print(f"[+] Successfully saved {count} tracks to database.")
            return True

        except Exception as e:
            print(f"[!] Error during scraping: {e}")
            return False

if __name__ == "__main__":
    scanner = SpotifyScanner(region='global')
    scanner.fetch_and_save()
