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

from concurrent.futures import ThreadPoolExecutor

def run_quant_report(market_context):
    """
    运行完整的市场量化分析报告（并行抓取版）。
    """
    print(f"--- PolyMusic 并行抓取启动: {market_context} ---", flush=True)
    
    # 获取绝对路径，防止目录混淆
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'data', 'polymusic.db')
    
    # 1. 定义抓取任务
    scanners = [
        SpotifyScanner(region='global', chart_type='daily'),
        SpotifyScanner(region='us', chart_type='daily'),
        SpotifyScanner(region='global', chart_type='weekly'),
        SpotifyScanner(region='us', chart_type='weekly')
    ]
    
    # 2. 并行执行抓取
    start_time = time.time()
    print("[*] 正在并行抓取 5 个榜单维度...", flush=True)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(s.fetch_and_save) for s in scanners]
        futures.append(executor.submit(SpotifyScanner().fetch_artists))
        
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"[!] 某个抓取线程执行出错: {e}", flush=True)
            
    print(f"[*] 所有数据抓取及入库完成，耗时: {time.time() - start_time:.2f}秒", flush=True)
    
    # 3. 提取分析数据
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT track_name, artist, streams FROM spotify_charts WHERE region = 'ww_weekly' AND position <= 3 ORDER BY position ASC")
    top_3 = cursor.fetchall()
    conn.close()
    
    spotify_summary = "\n".join([f"第{i+1}名: {r[0]} - {r[1]} ({r[2]:,} 流值)" for i, r in enumerate(top_3)])
    print(f"[*] Top 3 周榜分析:\n{spotify_summary}")

    # 3. 针对 3月6日 周五结算市场的专项量化
    if len(top_3) >= 2:
        leader_streams = top_3[0][2]
        contender_streams = top_3[1][2]
        # 假设今天是周三，距离周五结算还有约 2 天
        solver = AccumulationSolver(leader_streams, contender_streams, 2)
        gap = solver.calculate_gap()
        
        analysis_text = f"🚨 *3月6日结算情报*:\n第一名: {top_3[0][0]}\n第二名: {top_3[1][0]}\n反超缺口: 每日需追回 {gap:,.0f} 流值。"
        print(analysis_text, flush=True)
        
        # 4. AI 深度解读 (专门针对 3月6日 结算)
        ai_engine = MusicDecisionEngine()
        spotify_summary = f"目标市场：Spotify Global Weekly (March 6)\n数据：{top_3[0][0]} ({top_3[0][2]:,} total) vs {top_3[1][0]} ({top_3[1][2]:,} total)"
        viral_signals = "TikTok 数据显示第二名在周三下午有明显突破迹象"
        event_context = "Resolution Date: Mar 6. Market Source: Spotify Official."
        
        try:
            analysis = ai_engine.generate_analysis(spotify_summary, viral_signals, event_context)
            tg_text = f"🏆 *PolyMusic 博弈情报 (目标: 3月6日)*\n\n{analysis_text}\n\n*AI 建议*:\n{analysis}"
            send_telegram_message(tg_text)
        except Exception as e:
            print(f"AI Error: {e}", flush=True)

import time

if __name__ == "__main__":
    # Ensure DB is ready
    init_db()
    
    while True:
        try:
            # Example Market
            run_quant_report("3月6日 Spotify 全球周榜 结算博弈")
        except Exception as e:
            print(f"[!] Critical error in main loop: {e}")
        
        # 每天抓取并更新 4 次 (每 6 小时)
        print("[*] Waiting 6 hours for next update...")
        time.sleep(6 * 3600)
