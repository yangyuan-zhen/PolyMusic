from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import sqlite3
from src.data.database import init_db

app = FastAPI()

# 启动时初始化数据库
init_db()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

DB_PATH = os.path.join(BASE_DIR, "../data/polymusic.db")


def get_market_data():
    """获取 5 大博弈市场数据"""
    if not os.path.exists(DB_PATH):
        return {}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    markets = {}

    # 1. 全球周榜 (March 6)
    cursor.execute("""
        SELECT position, track_name, artist, streams FROM spotify_charts 
        WHERE region = 'weekly_song_global' ORDER BY position ASC LIMIT 10
    """)
    markets['global_weekly'] = cursor.fetchall()

    # 2. 美国周榜 (March 6)
    cursor.execute("""
        SELECT position, track_name, artist, streams FROM spotify_charts 
        WHERE region = 'weekly_song_us' ORDER BY position ASC LIMIT 10
    """)
    markets['us_weekly'] = cursor.fetchall()

    # 3. 2026 年度艺人 (基于总流值)
    cursor.execute("""
        SELECT position, artist, streams FROM spotify_charts 
        WHERE region = 'top_artists_total' ORDER BY position ASC LIMIT 10
    """)
    markets['top_artists_total'] = cursor.fetchall()

    # 4. 三月艺人排名 #1/#2 (基于月度听众)
    cursor.execute("""
        SELECT position, artist, streams FROM spotify_charts 
        WHERE region = 'monthly_listeners' ORDER BY position ASC LIMIT 10
    """)
    markets['monthly_rank'] = cursor.fetchall()

    conn.close()
    return markets


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    data = get_market_data()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "PolyMusic 精准博弈系统",
        "markets": data
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
