from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import sqlite3
from src.data.database import init_db

app = FastAPI()

# Ensure DB and tables exist on startup
init_db()

# Setup templates and static files
# We'll use a simple structure for now, injecting into the 'web' folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

DB_PATH = os.path.join(BASE_DIR, "../data/polymusic.db")

def get_db_data():
    if not os.path.exists(DB_PATH):
        return {}
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    charts = {}
    # Fetch different categories
    categories = {
        'ww_daily': '全球日榜',
        'us_daily': '美国日榜',
        'ww_weekly': '全球周榜',
        'us_weekly': '美国周榜',
        'top_artist': '热门艺人'
    }
    
    for cat_id, cat_name in categories.items():
        cursor.execute("SELECT position, track_name, artist, streams FROM spotify_charts WHERE region = ? ORDER BY position ASC LIMIT 10", (cat_id,))
        charts[cat_name] = cursor.fetchall()
        
    conn.close()
    return charts

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    data = get_db_data()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "PolyMusic 音乐市场量化分析",
        "charts": data
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
