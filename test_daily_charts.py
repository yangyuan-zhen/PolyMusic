import requests
from bs4 import BeautifulSoup
import re

headers = {"User-Agent": "Mozilla/5.0"}
def safe_int(text):
    cleaned = str(text).split('(')[0].split('*')[0]
    digits = re.sub(r'[^\d]', '', cleaned)
    return int(digits) if digits else 0

def check_kworb_daily(region):
    url = f"https://kworb.net/spotify/country/{region}_daily.html"
    print(f"\n--- Checking {url} ---")
    try:
        res = requests.get(url, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.find('table', {'class': 'sortable'}).find_all('tr')[1:11]
        for i, row in enumerate(rows, 1):
            cols = row.find_all('td')
            name = cols[2].text.strip()
            streams = safe_int(cols[5].text)
            print(f"#{i}: {name} ({streams:,})")
    except Exception as e:
        print(f"Error: {e}")

check_kworb_daily('global')
check_kworb_daily('us')
