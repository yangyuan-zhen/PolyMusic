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
        return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT date, track_name, artist, streams, position FROM spotify_charts ORDER BY date DESC, position ASC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    return rows

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    data = get_db_data()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "PolyMusic Quant Dashboard",
        "charts": data
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
