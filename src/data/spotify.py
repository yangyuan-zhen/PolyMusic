import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import os
import re


class SpotifyScanner:
    """
    专注 Polymarket 5 大博弈市场的数据采集器。
    数据源: kworb.net (Spotify 官方数据透传)
    """
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/polymusic.db')
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    def _safe_int(self, text):
        """安全提取数字，处理逗号、点号、括号等干扰"""
        cleaned = text.split('(')[0]  # 去掉 (x4) 之类
        digits = re.sub(r'[^\d]', '', cleaned)
        return int(digits) if digits else 0

    def _get_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        return conn, cursor

    # ========================================================
    # 市场 2: #1 song on Spotify this week (March 6) - 全球周榜
    # 市场 3: #1 song on US Spotify this week (March 6) - 美国周榜
    # ========================================================
    def fetch_weekly_songs(self, region='global'):
        """抓取周榜歌曲 Top 10"""
        region_code = 'global' if region == 'global' else 'us'
        url = f"https://kworb.net/spotify/country/{region_code}_weekly.html"
        market_id = f"weekly_song_{region_code}"
        
        print(f"[*] 抓取 {region} 周榜歌曲...", flush=True)
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            if not table:
                print(f"[!] {market_id}: 未找到表格", flush=True)
                return False

            rows = table.find_all('tr')[1:11]  # Top 10 就够了
            conn, cursor = self._get_db()
            today = datetime.now().strftime('%Y-%m-%d')

            for i, row in enumerate(rows, 1):
                cols = row.find_all('td')
                if len(cols) < 3:
                    continue

                # 歌曲名在第3列 (index 2)，格式: "Artist - Track"
                full_name = cols[2].text.strip()
                if " - " in full_name:
                    artist, track = full_name.split(" - ", 1)
                else:
                    artist, track = "Unknown", full_name

                # 从后往前找流值（最大的数字）
                streams = 0
                for col in reversed(cols):
                    val = self._safe_int(col.text.strip())
                    if val > 1000:  # 流值至少上千
                        streams = val
                        break

                cursor.execute('''
                    INSERT OR REPLACE INTO spotify_charts 
                    (date, region, position, track_name, artist, streams)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (today, market_id, i, track, artist, streams))

            conn.commit()
            conn.close()
            print(f"[+] {market_id}: 存入 {len(rows)} 条", flush=True)
            return True
        except Exception as e:
            print(f"[!] {market_id} 异常: {e}", flush=True)
            return False

    # ========================================================
    # 市场 1: Top Spotify Artist 2026 - 年度艺人
    # 市场 4: Top Spotify artist in March - 月度艺人第一
    # 市场 5: #2 Spotify artist in March - 月度艺人第二
    # ========================================================
    def fetch_top_artists(self):
        """抓取 Spotify 热门艺人排名（年度/月度通用）"""
        url = "https://kworb.net/spotify/artists.html"
        
        print("[*] 抓取热门艺人排名...", flush=True)
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            if not table:
                print("[!] 艺人表: 未找到表格", flush=True)
                return False

            rows = table.find_all('tr')[1:21]  # Top 20 艺人
            conn, cursor = self._get_db()
            today = datetime.now().strftime('%Y-%m-%d')

            for i, row in enumerate(rows, 1):
                cols = row.find_all('td')
                if len(cols) < 2:
                    continue

                # 艺人名通常在第一列，可能带链接
                name_tag = cols[0].find('a')
                name = name_tag.text.strip() if name_tag else cols[0].text.strip()

                # 从后往前找最大的数值作为总流值
                total_streams = 0
                daily_streams = 0
                for j, col in enumerate(cols[1:], 1):
                    val = self._safe_int(col.text.strip())
                    if val > total_streams:
                        total_streams = val
                    # 日均流值通常是较小的那个大数
                    if 100000 < val < total_streams:
                        daily_streams = val

                cursor.execute('''
                    INSERT OR REPLACE INTO spotify_charts 
                    (date, region, position, track_name, artist, streams)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (today, 'top_artists', i, f"daily:{daily_streams}", name, total_streams))

            conn.commit()
            conn.close()
            print(f"[+] 艺人榜: 存入 {len(rows)} 条", flush=True)
            return True
        except Exception as e:
            print(f"[!] 艺人榜异常: {e}", flush=True)
            return False

    def fetch_all_markets(self):
        """一次性抓取所有 5 个市场需要的数据"""
        from concurrent.futures import ThreadPoolExecutor
        import time

        start = time.time()
        print("=" * 50, flush=True)
        print("🎯 开始抓取 Polymarket 5 大音乐市场数据", flush=True)
        print("=" * 50, flush=True)

        with ThreadPoolExecutor(max_workers=3) as executor:
            f1 = executor.submit(self.fetch_weekly_songs, 'global')
            f2 = executor.submit(self.fetch_weekly_songs, 'us')
            f3 = executor.submit(self.fetch_top_artists)

            for f in [f1, f2, f3]:
                try:
                    f.result()
                except Exception as e:
                    print(f"[!] 线程异常: {e}", flush=True)

        print(f"✅ 全部数据同步完成，耗时: {time.time() - start:.2f}秒", flush=True)
        print("=" * 50, flush=True)


if __name__ == "__main__":
    scanner = SpotifyScanner()
    scanner.fetch_all_markets()
