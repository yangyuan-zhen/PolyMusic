import os
import sys
import time
import sqlite3
from dotenv import load_dotenv
from src.data.database import init_db
from src.data.spotify import HybridSpotifyScanner
from src.ai.prompt_engine import MusicDecisionEngine
import requests

load_dotenv()

def send_telegram_message(text):
    """推送消息到 Telegram"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram 推送失败: {e}", flush=True)

def get_market_data():
    """从数据库读取 5 大市场分类数据"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/polymusic.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    data = {}

    # 全球周榜歌曲
    cursor.execute("""
        SELECT position, track_name, artist, streams FROM spotify_charts 
        WHERE region = 'weekly_song_global' ORDER BY position ASC LIMIT 10
    """)
    data['global_weekly'] = cursor.fetchall()

    # 美国周榜歌曲
    cursor.execute("""
        SELECT position, track_name, artist, streams FROM spotify_charts 
        WHERE region = 'weekly_song_us' ORDER BY position ASC LIMIT 10
    """)
    data['us_weekly'] = cursor.fetchall()

    # 月度听众 (针对 Top Artist in March 市场)
    cursor.execute("""
        SELECT position, artist, streams FROM spotify_charts 
        WHERE region = 'monthly_listeners' ORDER BY position ASC LIMIT 10
    """)
    data['monthly_rank'] = cursor.fetchall()

    # 总榜艺人 (针对 Top Artist 2026 市场)
    cursor.execute("""
        SELECT position, artist, streams FROM spotify_charts 
        WHERE region = 'top_artists_total' ORDER BY position ASC LIMIT 10
    """)
    data['total_rank'] = cursor.fetchall()

    conn.close()
    return data

def run_market_analysis():
    print("\n🎯 开始抓取精准博弈数据...", flush=True)
    scanner = HybridSpotifyScanner()
    scanner.fetch_all_markets()

    data = get_market_data()
    
    # Debug print some values to log
    print(f"DEBUG: Global Weekly Top: {data['global_weekly'][:2] if data['global_weekly'] else 'EMPTY'}", flush=True)
    print(f"DEBUG: US Weekly Top: {data['us_weekly'][:2] if data['us_weekly'] else 'EMPTY'}", flush=True)
    print(f"DEBUG: Monthly Rank: {data['monthly_rank'][:2] if data['monthly_rank'] else 'EMPTY'}", flush=True)
    print(f"DEBUG: Total Rank: {data['total_rank'][:2] if data['total_rank'] else 'EMPTY'}", flush=True)
    report = ["🏆 *PolyMusic 精准博弈报告*\n"]

    # 全球歌曲市场分析
    if data['global_weekly']:
        leader = data['global_weekly'][0]
        report.append(f"*📊 #1 Song Global (Mar 6)*: {leader[2]} - {leader[1]} ({leader[3]:,} streams/week)")

    # 美国歌曲市场分析
    if data['us_weekly']:
        leader = data['us_weekly'][0]
        report.append(f"*🇺🇸 #1 Song US (Mar 6)*: {leader[2]} - {leader[1]} ({leader[3]:,} streams/week)")

    # 3月艺人市场分析
    if data['monthly_rank']:
        m1 = data['monthly_rank'][0]
        m2 = data['monthly_rank'][1]
        report.append(f"\n*👑 Top Artist March:* #1 {m1[1]} ({m1[2]:,}), #2 {m2[1]} ({m2[2]:,})")

    # 2026 艺人市场分析
    if data['total_rank']:
        t1 = data['total_rank'][0]
        report.append(f"*🎤 2026 Top Artist Total:* #1 {t1[1]} ({t1[2]:,} total)")

    report_text = "\n".join(report)
    print(report_text, flush=True)
    send_telegram_message(report_text)

    # 发送给 AI 深入解读
    if data['monthly_rank']:
        try:
            ai_engine = MusicDecisionEngine()
            context = f"Top Monthly: {data['monthly_rank'][:3]}, Top Weekly US: {data['us_weekly'][:3]}"
            analysis = ai_engine.generate_analysis(context, "Polymarket March Artist Market", "Resolution: March 31")
            send_telegram_message(f"🤖 *AI 分析建议*:\n{analysis}")
        except Exception as e:
            print(f"AI Error: {e}", flush=True)

if __name__ == "__main__":
    init_db()
    while True:
        try:
            run_market_analysis()
        except Exception as e:
            print(f"Error: {e}", flush=True)
        time.sleep(6 * 3600)
