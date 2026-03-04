import requests
from bs4 import BeautifulSoup
import re

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def debug_url(name, url):
    print(f"\n--- Debugging {name}: {url} ---")
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table', {'class': 'sortable'})
        if not table:
            print("No table found!")
            return
        
        rows = table.find_all('tr')
        print(f"Total rows: {len(rows)}")
        
        # Print header
        header = rows[0].find_all(['th', 'td'])
        print(f"Header columns ({len(header)}): {[c.text.strip() for c in header]}")
        
        # Print first data row
        if len(rows) > 1:
            first_row = rows[1].find_all('td')
            print(f"Row 1 columns ({len(first_row)}): {[c.text.strip() for c in first_row]}")
            
    except Exception as e:
        print(f"Error: {e}")

debug_url("Global Weekly", "https://kworb.net/spotify/country/global_weekly.html")
debug_url("US Weekly", "https://kworb.net/spotify/country/us_weekly.html")
debug_url("Monthly Listeners", "https://kworb.net/spotify/listeners.html")
debug_url("Total Artists", "https://kworb.net/spotify/artists.html")
