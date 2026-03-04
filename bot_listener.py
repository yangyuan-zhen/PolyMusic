import os
import sys
import time
import sqlite3
from dotenv import load_dotenv
from src.data.database import init_db
from src.data.spotify import SpotifyScanner
from src.analysis.accumulation import AccumulationSolver
from src.ai.prompt_engine import MusicDecisionEngine
import requests

load_dotenv()


def send_telegram_message(text):
    """推送消息到 Telegram"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[!] Telegram 配置缺失", flush=True)
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
        print("[+] Telegram 推送成功", flush=True)
    except Exception as e:
        print(f"[!] Telegram 推送失败: {e}", flush=True)


def get_market_data():
    """从数据库读取 5 大市场数据"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/polymusic.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    data = {}

    # 市场 2: 全球周榜歌曲
    cursor.execute("""
        SELECT position, track_name, artist, streams 
        FROM spotify_charts WHERE region = 'weekly_song_global' 
        ORDER BY position ASC LIMIT 10
    """)
    data['global_weekly'] = cursor.fetchall()

    # 市场 3: 美国周榜歌曲
    cursor.execute("""
        SELECT position, track_name, artist, streams 
        FROM spotify_charts WHERE region = 'weekly_song_us' 
        ORDER BY position ASC LIMIT 10
    """)
    data['us_weekly'] = cursor.fetchall()

    # 市场 1, 4, 5: 艺人排名
    cursor.execute("""
        SELECT position, track_name, artist, streams 
        FROM spotify_charts WHERE region = 'top_artists' 
        ORDER BY position ASC LIMIT 20
    """)
    data['artists'] = cursor.fetchall()

    conn.close()
    return data


def run_market_analysis():
    """运行 5 大博弈市场分析"""
    print("\n🎯 PolyMusic 博弈情报系统启动", flush=True)
    print("=" * 50, flush=True)

    # 1. 抓取数据
    scanner = SpotifyScanner()
    scanner.fetch_all_markets()

    # 2. 读取数据
    data = get_market_data()

    # 3. 构建情报
    report_lines = ["🏆 *PolyMusic 博弈情报*\n"]

    # --- 市场 2: 全球周榜 #1 ---
    report_lines.append("*📀 市场: #1 Song Global (March 6)*")
    if data['global_weekly']:
        for row in data['global_weekly'][:5]:
            pos, track, artist, streams = row
            s = f"{streams:,}" if streams else "N/A"
            report_lines.append(f"  #{pos} {track} - {artist} ({s})")
    else:
        report_lines.append("  暂无数据")

    # --- 市场 3: 美国周榜 #1 ---
    report_lines.append("\n*🇺🇸 市场: #1 Song US (March 6)*")
    if data['us_weekly']:
        for row in data['us_weekly'][:5]:
            pos, track, artist, streams = row
            s = f"{streams:,}" if streams else "N/A"
            report_lines.append(f"  #{pos} {track} - {artist} ({s})")
    else:
        report_lines.append("  暂无数据")

    # --- 市场 1, 4, 5: 艺人排名 ---
    report_lines.append("\n*🎤 市场: Top Artist 2026 / March #1 / March #2*")
    if data['artists']:
        for row in data['artists'][:10]:
            pos, daily_info, name, total = row
            s = f"{total:,}" if total else "N/A"
            report_lines.append(f"  #{pos} {name} ({s})")
    else:
        report_lines.append("  暂无数据")

    report_text = "\n".join(report_lines)
    print(report_text, flush=True)

    # 4. 推送 Telegram
    send_telegram_message(report_text)

    # 5. AI 分析 (如果有数据)
    if data['global_weekly'] and data['artists']:
        try:
            ai_engine = MusicDecisionEngine()
            context = f"""
目标: Polymarket 5 大音乐市场博弈分析
全球周榜 Top 3: {data['global_weekly'][:3]}
美国周榜 Top 3: {data['us_weekly'][:3]}
艺人 Top 5: {data['artists'][:5]}
当前市场赔率:
- 全球周榜#1: 85% Stateside+Zara Larsson
- 美国周榜#1: 5% Stateside+Zara Larsson  
- 年度艺人: 57% Bad Bunny
- 3月艺人#1: 93% Bruno Mars
- 3月艺人#2: 59% The Weeknd
"""
            analysis = ai_engine.generate_analysis(context, "Polymarket赔率数据", "结算日: March 6 (周榜), March 31 (月度)")
            ai_report = f"\n\n🤖 *AI 博弈建议*:\n{analysis}"
            send_telegram_message(ai_report)
        except Exception as e:
            print(f"[!] AI 分析异常: {e}", flush=True)


if __name__ == "__main__":
    init_db()

    while True:
        try:
            run_market_analysis()
        except Exception as e:
            print(f"[!] 主循环异常: {e}", flush=True)

        print("\n⏰ 等待 6 小时后下次更新...", flush=True)
        time.sleep(6 * 3600)
