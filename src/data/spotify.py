import requests
import json
import sqlite3
import os
from datetime import datetime
from bs4 import BeautifulSoup
import re

class HybridSpotifyScanner:
    """
    混合数据抓取器：
    1. 歌曲周榜 (March 6): 官方 Spotify Charts HTML 解析 (最权威)
    2. 艺人听众排名 (March & 2026): Kworb (Polymarket 官方指定结算源)
    """
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/polymusic.db')
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        return conn, cursor

    def _safe_int(self, text):
        cleaned = str(text).split('(')[0].split('*')[0]
        digits = re.sub(r'[^\d]', '', cleaned)
        return int(digits) if digits else 0

    def fetch_official_weekly_songs(self, region='global'):
        """
        通过解析 Spotify 官方 Charts 网页的 JSON Blob 抓取周榜 (绕过 API 拦截)
        区号: global 或者是 us
        """
        region_code = 'global' if region == 'global' else 'us'
        market_id = f"weekly_song_{region_code}"
        
        print(f"[*] 解析 Spotify 官方图表 {region} 周榜...", flush=True)
        try:
            url = f"https://charts.spotify.com/charts/view/regional-{region_code}-weekly/latest"
            res = requests.get(url, headers=self.headers, timeout=15)
            
            if res.status_code != 200:
                print(f"[!] 官方页面访问失败 ({res.status_code})。尝试备用解析方案...", flush=True)
                return self._fallback_fetch_weekly_songs(region)

            # 解析 Next.js 注入的数据
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', res.text)
            if not match:
                print(f"[!] 无法在 HTML 中找到 JSON 数据。尝试备用解析方案...", flush=True)
                return self._fallback_fetch_weekly_songs(region)

            data = json.loads(match.group(1))
            
            # 层级很深，寻找 chart entries
            try:
                # __NEXT_DATA__ -> props -> pageProps -> initialStoreState -> chart -> entries
                entries = data['props']['pageProps']['initialStoreState']['chart']['entries']
            except KeyError:
                 print(f"[!] JSON 数据结构已更改。尝试备用解析方案...", flush=True)
                 return self._fallback_fetch_weekly_songs(region)
            
            conn, cursor = self._get_db()
            today = datetime.now().strftime('%Y-%m-%d')
            count = 0

            # 取前 20 名
            for i, entry in enumerate(entries[:20], 1):
                track_name = entry.get("trackMetadata", {}).get("trackName", "Unknown")
                artists = entry.get("trackMetadata", {}).get("artists", [])
                artist_name = artists[0].get("name", "Unknown") if artists else "Unknown"
                streams = entry.get("chartEntryData", {}).get("streams", 0)

                if streams == 0:
                    try:
                        # 有时候在别的地方
                        streams = entry['chartEntryData']["chartEntryData"]['streams']
                    except:
                        pass

                cursor.execute('''
                    INSERT OR REPLACE INTO spotify_charts (date, region, position, track_name, artist, streams)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (today, market_id, i, track_name, artist_name, streams))
                count += 1

            conn.commit()
            conn.close()
            print(f"[+] {market_id}: 官方数据获取成功 ({count}条)", flush=True)
            return True

        except Exception as e:
            print(f"[!] 官方网络加载异常 ({e})。尝试备用解析方案...", flush=True)
            return self._fallback_fetch_weekly_songs(region)

    def _fallback_fetch_weekly_songs(self, region):
        """备用方案: 抓取 kworb"""
        region_code = 'global' if region == 'global' else 'us'
        market_id = f"weekly_song_{region_code}"
        print(f"[*] 启用备用方案抓取 Kworb {region} 周榜...", flush=True)
        url = f"https://kworb.net/spotify/country/{region_code}_weekly.html"
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            if not table: return False

            rows = table.find_all('tr')[1:21]
            conn, cursor = self._get_db()
            today = datetime.now().strftime('%Y-%m-%d')
            count = 0

            for i, row in enumerate(rows, 1):
                cols = row.find_all('td')
                if len(cols) < 7: continue

                full_name = cols[2].text.strip()
                artist, track = full_name.split(" - ", 1) if " - " in full_name else ("Unknown", full_name)
                
                # 寻找真实的周流值
                weekly_streams = 0
                for col in cols[3:]:
                    val = self._safe_int(col.text)
                    if (region == 'global' and 5000000 < val < 200000000) or \
                       (region == 'us' and 1000000 < val < 50000000):
                        weekly_streams = val
                        break
                
                # 如果没找到合适的，就用第5列（通常是周流值所在列）
                if weekly_streams == 0 and len(cols) > 5:
                    weekly_streams = self._safe_int(cols[5].text)

                cursor.execute('''
                    INSERT OR REPLACE INTO spotify_charts (date, region, position, track_name, artist, streams)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (today, market_id, i, track, artist, weekly_streams))
                count += 1

            conn.commit()
            conn.close()
            print(f"[+] {market_id}: 备用数据同步成功 ({count}条)", flush=True)
            return True
        except Exception as e:
            print(f"[!] 备用方案异常: {e}", flush=True)
            return False

    def fetch_kworb_monthly_listeners(self):
        """抓取月度听众 (针对 March#1/March#2 市场)"""
        url = "https://kworb.net/spotify/listeners.html"
        print("[*] 从 Kworb 抓取月度听众 (Polymarket 标准)...", flush=True)
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            rows = table.find_all('tr')[1:21]
            
            conn, cursor = self._get_db()
            today = datetime.now().strftime('%Y-%m-%d')
            count = 0
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3: continue
                
                pos = self._safe_int(cols[0].text.strip())
                name = cols[1].text.strip()
                listeners = self._safe_int(cols[2].text.strip())
                
                if listeners > 0:
                    cursor.execute('''
                        INSERT OR REPLACE INTO spotify_charts (date, region, position, track_name, artist, streams)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (today, 'monthly_listeners', pos, 'MONTHLY', name, listeners))
                    count += 1
            
            conn.commit()
            conn.close()
            print(f"[+] 月度听众同步成功 ({count}条)", flush=True)
            return True
        except Exception as e:
            print(f"[!] 月度听众异常: {e}", flush=True)
            return False

    def fetch_kworb_top_artists(self):
        """抓取总榜 (针对 2026 年度艺人市场)"""
        url = "https://kworb.net/spotify/artists.html"
        print("[*] 从 Kworb 抓取艺人总榜...", flush=True)
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            rows = table.find_all('tr')[1:21]
            
            conn, cursor = self._get_db()
            today = datetime.now().strftime('%Y-%m-%d')
            count = 0
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3: continue
                
                pos = self._safe_int(cols[0].text.strip())
                name = cols[1].text.strip()
                total = self._safe_int(cols[2].text.strip())
                
                if total > 0:
                    cursor.execute('''
                        INSERT OR REPLACE INTO spotify_charts (date, region, position, track_name, artist, streams)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (today, 'top_artists_total', pos, 'TOTAL', name, total))
                    count += 1
            
            conn.commit()
            conn.close()
            print(f"[+] 艺人总榜同步成功 ({count}条)", flush=True)
            return True
        except Exception as e:
            print(f"[!] 艺人总榜异常: {e}", flush=True)
            return False

    def fetch_all_markets(self):
        self.fetch_official_weekly_songs('global')
        self.fetch_official_weekly_songs('us')
        self.fetch_kworb_monthly_listeners()
        self.fetch_kworb_top_artists()

if __name__ == "__main__":
    scanner = HybridSpotifyScanner()
    scanner.fetch_all_markets()
