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
    Run a full quant analysis for a given market.
    """
    print(f"--- PolyMusic Report for: {market_context} ---")
    
    # 1. Fetch Real Data from Spotify (Kworb)
    scanner = SpotifyScanner(region='global')
    scanner.fetch_and_save()
    
    # 2. Extract Data for Analysis
    conn = sqlite3.connect(scanner.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT track_name, artist, streams FROM spotify_charts WHERE position <= 3 ORDER BY position ASC")
    top_3 = cursor.fetchall()
    conn.close()
    
    spotify_summary = "\n".join([f"#{i+1}: {r[0]} by {r[1]} ({r[2]:,} streams)" for i, r in enumerate(top_3)])
    print(f"[*] Top 3 Analysis:\n{spotify_summary}")

    # 3. Accumulation Analysis (Example: Top 1 vs Top 2)
    if len(top_3) >= 2:
        leader_streams = top_3[0][2]
        contender_streams = top_3[1][2]
        # Mocking weekly gap: current day 4 of 7
        solver = AccumulationSolver(leader_streams * 7, contender_streams * 4, 3)
        gap = solver.calculate_gap()
        print(f"Accumulation Gap: {gap:,.0f} daily streams needed to flip Top 1.")
    
    # 4. AI Insights
    ai_engine = MusicDecisionEngine()
    viral_signals = "TikTok Growth: Stable on Top 1, High acceleration on Top 3 bridge snippet"
    event_context = "SNL Performance pending for Top 2 Artist"
    
    try:
        analysis = ai_engine.generate_analysis(spotify_summary, viral_signals, event_context)
        print("\n--- AI QUANT ANALYSIS ---")
        print(analysis)
        
        # 5. Push to Telegram
        tg_text = f"🎵 *PolyMusic Report: {market_context}*\n\n{analysis}"
        send_telegram_message(tg_text)
        
    except Exception as e:
        print(f"\nAI Engine Error: {e}")

if __name__ == "__main__":
    # Ensure DB is ready
    if not os.path.exists("./data/polymusic.db"):
        init_db()
        
    # Example Market
    run_quant_report("Billboard Hot 100 Week of March 6")
