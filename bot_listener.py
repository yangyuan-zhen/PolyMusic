import os
import sys
from dotenv import load_dotenv
from src.data.database import init_db
from src.analysis.accumulation import AccumulationSolver
from src.ai.prompt_engine import MusicDecisionEngine

from src.data.spotify import SpotifyScanner
import sqlite3
import requests

load_dotenv()

def send_telegram_message(text):
    """
    Sends a message to the configured Telegram chat.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[!] Telegram config missing.")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
        print("[+] Telegram notification sent.")
    except Exception as e:
        print(f"[!] Failed to send Telegram: {e}")

def run_quant_report(market_context):
    """
    运行完整的市场量化分析报告。
    """
    print(f"--- PolyMusic Report for: {market_context} ---")
    
    # 1. 抓取多维度数据
    # Global Daily
    SpotifyScanner(region='global', chart_type='daily').fetch_and_save()
    # US Daily
    SpotifyScanner(region='us', chart_type='daily').fetch_and_save()
    # Global Weekly
    SpotifyScanner(region='global', chart_type='weekly').fetch_and_save()
    # US Weekly
    SpotifyScanner(region='us', chart_type='weekly').fetch_and_save()
    # Top Artists
    SpotifyScanner().fetch_artists()
    
    # 2. 提取分析数据 (以全球周榜为例)
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'data/polymusic.db'))
    cursor = conn.cursor()
    cursor.execute("SELECT track_name, artist, streams FROM spotify_charts WHERE region = 'ww_weekly' AND position <= 3 ORDER BY position ASC")
    top_3 = cursor.fetchall()
    conn.close()
    
    spotify_summary = "\n".join([f"第{i+1}名: {r[0]} - {r[1]} ({r[2]:,} 流值)" for i, r in enumerate(top_3)])
    print(f"[*] Top 3 周榜分析:\n{spotify_summary}")

    # 3. 积分缺口分析
    if len(top_3) >= 2:
        leader_streams = top_3[0][2]
        contender_streams = top_3[1][2]
        solver = AccumulationSolver(leader_streams, contender_streams, 3)
        gap = solver.calculate_gap()
        print(f"积分缺口: 每日需 {gap:,.0f} 流值即可反超。")
    
    # 4. AI 深度解读
    ai_engine = MusicDecisionEngine()
    viral_signals = "TikTok 增长：第一名稳定，第三名副歌片段爆发式增长"
    event_context = "第二名艺人本周末有 SNL 表演预热"
    
    try:
        analysis = ai_engine.generate_analysis(spotify_summary, viral_signals, event_context)
        # 5. 推送至电报
        tg_text = f"🎵 *PolyMusic 市场量化报告: {market_context}*\n\n{analysis}"
        send_telegram_message(tg_text)
    except Exception as e:
        print(f"\nAI Engine Error: {e}")

if __name__ == "__main__":
    # Ensure DB is ready
    if not os.path.exists("./data/polymusic.db"):
        init_db()
        
    # Example Market
    run_quant_report("Billboard Hot 100 Week of March 6")
