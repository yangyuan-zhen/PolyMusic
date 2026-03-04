import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import os
import re

class SpotifyScanner:
    """
    专注 Polymarket 5 大博弈市场的数据采集器 (修正版)。
    精准区分：月度听众 (Listeners) 与 周/总流值 (Weekly/Total Streams)。
    """
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/polymusic.db')
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    def _safe_int(self, text):
        """安全提取数字"""
        cleaned = text.split('(')[0]
        digits = re.sub(r'[^\d]', '', cleaned)
        return int(digits) if digits else 0

    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        return conn, cursor

    def fetch_weekly_songs(self, region='global'):
        """抓取周榜歌曲 (区分周流值与总流值)"""
        region_code = 'global' if region == 'global' else 'us'
        url = f"https://kworb.net/spotify/country/{region_code}_weekly.html"
        market_id = f"weekly_song_{region_code}"
        
        print(f"[*] 抓取 {region} 周榜...", flush=True)
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            if not table: return False

            rows = table.find_all('tr')[1:21] # 取 Top 20
            conn, cursor = self._get_db()
            today = datetime.now().strftime('%Y-%m-%d')

            for i, row in enumerate(rows, 1):
                cols = row.find_all('td')
                if len(cols) < 6: continue

                full_name = cols[2].text.strip()
                artist, track = full_name.split(" - ", 1) if " - " in full_name else ("Unknown", full_name)

                # 重点：Kworb 周榜表格结构
                # Index 3: Weekly Streams (我们要的)
                # Index 5 或最后: Total Streams (历史累计)
                weekly_streams = self._safe_int(cols[3].text.strip())
                # 如果第3列没拿到，尝试找倒数第二列
                if weekly_streams == 0:
                    weekly_streams = self._safe_int(cols[-3].text.strip())

                cursor.execute('''
                    INSERT OR REPLACE INTO spotify_charts 
                    (date, region, position, track_name, artist, streams)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (today, market_id, i, track, artist, weekly_streams))

            conn.commit()
            conn.close()
            print(f"[+] {market_id}: 同步完成", flush=True)
            return True
        except Exception as e:
            print(f"[!] {market_id} 异常: {e}", flush=True)
            return False

    def fetch_monthly_listeners(self):
        """抓取月度听众排名 (针对 March#1/March#2 市场)"""
        url = "https://kworb.net/spotify/listeners.html"
        print("[*] 抓取月度听众 (Monthly Listeners)...", flush=True)
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            rows = table.find_all('tr')[1:21]
            
            conn, cursor = self._get_db()
            today = datetime.now().strftime('%Y-%m-%d')
            for i, row in enumerate(rows, 1):
                cols = row.find_all('td')
                if len(cols) < 2: continue
                
                name = cols[0].text.strip()
                listeners = self._safe_int(cols[1].text.strip())
                
                cursor.execute('''
                    INSERT OR REPLACE INTO spotify_charts 
                    (date, region, position, track_name, artist, streams)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (today, 'monthly_listeners', i, 'MONTHLY_STATS', name, listeners))
            
            conn.commit()
            conn.close()
            print("[+] 月度听众同步完成", flush=True)
            return True
        except Exception as e:
            print(f"[!] 月度听众异常: {e}", flush=True)
            return False

    def fetch_top_artists(self):
        """抓取总流值排名 (针对 2026 Artist 市场)"""
        url = "https://kworb.net/spotify/artists.html"
        print("[*] 抓取艺人总流值 (Total Streams)...", flush=True)
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            rows = table.find_all('tr')[1:21]
            
            conn, cursor = self._get_db()
            today = datetime.now().strftime('%Y-%m-%d')
            for i, row in enumerate(rows, 1):
                cols = row.find_all('td')
                if len(cols) < 2: continue
                
                name = cols[0].text.strip()
                total_streams = self._safe_int(cols[1].text.strip())
                
                cursor.execute('''
                    INSERT OR REPLACE INTO spotify_charts 
                    (date, region, position, track_name, artist, streams)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (today, 'top_artists_total', i, 'TOTAL_STATS', name, total_streams))
            
            conn.commit()
            conn.close()
            print("[+] 艺人总榜同步完成", flush=True)
            return True
        except Exception as e:
            print(f"[!] 艺人总榜异常: {e}", flush=True)
            return False

    def fetch_all_markets(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.submit(self.fetch_weekly_songs, 'global')
            executor.submit(self.fetch_weekly_songs, 'us')
            executor.submit(self.fetch_monthly_listeners)
            executor.submit(self.fetch_top_artists)
