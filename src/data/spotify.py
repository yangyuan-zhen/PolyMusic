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
        """智能列识别的多维度榜单爬虫"""
        headers = {"User-Agent": "Mozilla/5.0"}
        category = f"{self.region_code}_{self.chart_type}"
        print(f"[*] 正在抓取 {category} 榜单: {self.base_url}", flush=True)
        try:
            response = requests.get(self.base_url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'class': 'sortable'})
            if not table: 
                print(f"[!] 未找到 {category} 的数据表", flush=True)
                return False
                
            rows = table.find_all('tr')
            if len(rows) < 2: return False
            
            # 第一行通常是表头，我们也看一眼数据行
            sample_cols = rows[1].find_all('td')
            
            today_str = datetime.now().strftime('%Y-%m-%d')
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            count = 0
            for row in rows[1:101]:
                cols = row.find_all('td')
                if len(cols) < 3: continue
                
                # 1. 提取排名 (首列)
                pos_text = re.sub(r'[^\d]', '', cols[0].text.strip())
                pos = int(pos_text) if pos_text else 0
                
                # 2. 提取曲名与艺人 (通常在索引 2)
                full_name = cols[2].text.strip()
                if " - " in full_name:
                    artist, track = full_name.split(" - ", 1)
                else:
                    artist, track = "Unknown", full_name
                
                # 3. 智能寻找流值列 (从后往前找第一个带数字的有效列)
                streams = 0
                for col in reversed(cols):
                    val_text = col.text.strip().split('(')[0] # 去掉 (x4)
                    clean_val = re.sub(r'[^\d]', '', val_text)
                    if clean_val and len(clean_val) > 2: # 过滤掉天数之类的小数字
                        streams = int(clean_val)
                        break
                
                cursor.execute('''
                    INSERT OR REPLACE INTO spotify_charts (date, region, position, track_name, artist, streams)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (today_str, category, pos, track, artist, streams))
                count += 1
            
            conn.commit()
            conn.close()
            print(f"[+] {category} 同步成功，存入 {count} 条数据", flush=True)
            return True
        except Exception as e:
            print(f"[!] {category} 抓取异常: {e}", flush=True)
            return False

if __name__ == "__main__":
    scanner = SpotifyScanner(region='global')
    scanner.fetch_and_save()
