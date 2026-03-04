import requests
from bs4 import BeautifulSoup
import re

headers = {"User-Agent": "Mozilla/5.0"}

url = "https://kworb.net/spotify/country/global_daily.html"
res = requests.get(url, headers=headers)
res.encoding = 'utf-8'
soup = BeautifulSoup(res.text, 'html.parser')
rows = soup.find('table', {'class': 'sortable'}).find_all('tr')[1:5]
for i, row in enumerate(rows, 1):
    cols = row.find_all('td')
    col_texts = [c.text.strip() for c in cols]
    print(f"Row {i}: {col_texts}")
