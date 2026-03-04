import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import os
import re

class SpotifyScanner:
    """
    针对 Kworb 表格结构的终极对位爬虫。
    周榜: Index 5 = Weekly Streams
    听众/艺人: Index 1 = Name, Index 2 = Value
    """
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/polymusic.db')
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    def _safe_int(self, text):
        cleaned = text.split('(')[0].split('*')[0]
        digits = re.sub(r'[^\d]', '', cleaned)
        return int(digits) if digits else 0

    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        return conn, cursor

    def fetch_weekly_songs(self, region='global'):
        """抓取周榜歌曲 (Index 5 是周流值)"""
        region_code = 'global' if region == 'global' else 'us'
        url = f"https://kworb.net/spotify/country/{region_code}_weekly.html"
        market_id = f"weekly_song_{region_code}"
        
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            if not table: return False

            rows = table.find_all('tr')[1:21]
            conn, cursor = self._get_db()
            today = datetime.now().strftime('%Y-%m-%d')

            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 7: continue

                pos = self._safe_int(cols[0].text.strip())
                full_name = cols[2].text.strip()
                artist, track = full_name.split(" - ", 1) if " - " in full_name else ("Unknown", full_name)
                
                # 精准对位：Index 5 是 Weekly Streams
                weekly_streams = self._safe_int(cols[5].text.strip())

                cursor.execute('''
                    INSERT OR REPLACE INTO spotify_charts (date, region, position, track_name, artist, streams)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (today, market_id, pos, track, artist, weekly_streams))

            conn.commit()
            conn.close()
            print(f"[+] {market_id}: 同步成功", flush=True)
            return True
        except Exception as e:
            print(f"[!] {market_id} 错误: {e}", flush=True)
            return False

    def fetch_monthly_listeners(self):
        """抓取月度听众 (Index 1 是名字, Index 2 是听众数)"""
        url = "https://kworb.net/spotify/listeners.html"
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            rows = table.find_all('tr')[1:21]
            
            conn, cursor = self._get_db()
            today = datetime.now().strftime('%Y-%m-%d')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3: continue
                
                pos = self._safe_int(cols[0].text.strip())
                name = cols[1].text.strip() # Index 1 是名字
                listeners = self._safe_int(cols[2].text.strip()) # Index 2 是流值
                
                cursor.execute('''
                    INSERT OR REPLACE INTO spotify_charts (date, region, position, track_name, artist, streams)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (today, 'monthly_listeners', pos, 'MONTHLY', name, listeners))
            
            conn.commit()
            conn.close()
            print("[+] 月度听众: 同步成功", flush=True)
            return True
        except Exception as e:
            print(f"[!] 月度听众错误: {e}", flush=True)
            return False

    def fetch_top_artists(self):
        """抓取艺人总榜 (Index 1 是名字, Index 2 是总流值)"""
        url = "https://kworb.net/spotify/artists.html"
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            rows = table.find_all('tr')[1:21]
            
            conn, cursor = self._get_db()
            today = datetime.now().strftime('%Y-%m-%d')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3: continue
                
                pos = self._safe_int(cols[0].text.strip())
                name = cols[1].text.strip()
                total = self._safe_int(cols[2].text.strip())
                
                cursor.execute('''
                    INSERT OR REPLACE INTO spotify_charts (date, region, position, track_name, artist, streams)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (today, 'top_artists_total', pos, 'TOTAL', name, total))
            
            conn.commit()
            conn.close()
            print("[+] 艺人总榜: 同步成功", flush=True)
            return True
        except Exception as e:
            print(f"[!] 艺人总榜错误: {e}", flush=True)
            return False
