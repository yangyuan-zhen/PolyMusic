import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import os
import re

class SpotifyScanner:
    """
    终极稳定版爬虫 - 自动探测列结构。
    通过正则和数值特征自动识别：名字、周流值、月度听众、年度总流值。
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

    def _scrape_generic(self, url, market_id, name_index=None, value_index=None, is_weekly=False):
        """通用抓取逻辑，带自动列探测"""
        print(f"[*] 正在抓取: {url}", flush=True)
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            if not table: return False

            rows = table.find_all('tr')
            conn, cursor = self._get_db()
            today = datetime.now().strftime('%Y-%m-%d')
            count = 0

            for row in rows[1:51]: # 只看前 50 名
                cols = row.find_all('td')
                if len(cols) < 3: continue

                # 1. 提取排名 (永远是第一列)
                pos = self._safe_int(cols[0].text.strip())
                
                # 2. 提取艺人/曲名
                # 逻辑：跳过排名字段，找第一个包含链接或长文本的列
                name = ""
                potential_name_cols = [2, 1, 3] # 常用索引
                found_name = False
                for idx in potential_name_cols:
                    if idx < len(cols):
                        text = cols[idx].text.strip()
                        if len(text) > 3: # 排除 P+ 之类的短标志
                            name = text
                            found_name = True
                            break
                if not found_name: name = "Unknown"

                # 3. 寻找数值 (流值/听众)
                # 策略：
                # 周榜博弈：我们需要第一个 > 100,000 的数字（过滤掉天数、排名）
                # 艺人榜：我们需要最大的那个数（月度听众或总流值）
                nums = []
                for j, col in enumerate(cols):
                    val = self._safe_int(col.text.strip())
                    if val > 100: # 排除排名、变化等小数字
                        nums.append(val)
                
                value = 0
                if is_weekly:
                    # 周榜通常第一个大数是周流值，第二个大数是总流值
                    if len(nums) >= 1: value = nums[0]
                else:
                    # 艺人榜通常只有一两个大数，取大的
                    if nums: value = max(nums)

                # 特殊处理：如果抓取到了 15 亿这种总流值，而我们在抓周榜，则尝试找一个稍小的数
                if is_weekly and value > 100000000: # 如果周流值超过1亿，极有可能是总流值
                    for n in nums:
                        if 500000 < n < 100000000: # 真实的周榜范围
                            value = n
                            break

                # 数据库入库
                if " - " in name:
                    artist, track = name.split(" - ", 1)
                else:
                    artist, track = name, "N/A"

                cursor.execute('''
                    INSERT OR REPLACE INTO spotify_charts (date, region, position, track_name, artist, streams)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (today, market_id, pos, track, artist, value))
                count += 1

            conn.commit()
            conn.close()
            print(f"[+] {market_id}: 成功抓取 {count} 条", flush=True)
            return True
        except Exception as e:
            print(f"[!] {market_id} 异常: {e}", flush=True)
            return False

    def fetch_weekly_songs(self, region='global'):
        region_code = 'global' if region == 'global' else 'us'
        url = f"https://kworb.net/spotify/country/{region_code}_weekly.html"
        return self._scrape_generic(url, f"weekly_song_{region_code}", is_weekly=True)

    def fetch_monthly_listeners(self):
        url = "https://kworb.net/spotify/listeners.html"
        return self._scrape_generic(url, 'monthly_listeners')

    def fetch_top_artists(self):
        url = "https://kworb.net/spotify/artists.html"
        return self._scrape_generic(url, 'top_artists_total')

    def fetch_all_markets(self):
        # 顺序执行，防止并发冲突
        self.fetch_weekly_songs('global')
        self.fetch_weekly_songs('us')
        self.fetch_monthly_listeners()
        self.fetch_top_artists()
