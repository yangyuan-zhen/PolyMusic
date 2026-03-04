# PolyMusic 🎵

A real-time quantitative dashboard designed explicitly to track specific Spotify music metrics related to Polymarket cryptocurrency prediction markets.

![Dashboard Overview](docs/dashboard.png)

## Why PolyMusic?

Polymarket music charts are highly specific about how they resolve their markets. This tool bridges the gap between active Polymarket outcomes and actual streaming data:

1. **Song Markets (#1 Global / #1 US)**: Resolves using the official Spotify API `open.spotify.com`. Because players bet on the _upcoming_ weekly outcomes, PolyMusic tracks the **Daily Real-Time Streams (Live)** straight from the bleeding-edge Next.js injection on `charts.spotify.com` to project the eventual weekly winner precisely.
2. **Artist Markets (March Top Artist & 2026 Total)**: Resolves specifically utilizing Kworb data (`kworb.net/spotify/listeners.html` and `kworb.net/spotify/artists.html`). PolyMusic automatically falls back to these specific Kworb pages to provide 100% resolution-source accuracy.

## 🎯 Target Polymarket Markets

Currently tracking 5 active dimensions:

- #1 song on Spotify this week? (Global)
- #1 song on US Spotify this week? (US)
- Top Spotify Artist in March?
- #2 Spotify Artist in March?
- Top Spotify Artist 2026

## 🚀 Deployment

We provide a streamlined one-click deployment script using Docker Compose that seamlessly manages the data scrapers, SQLite database, and the web server.

### Prerequisites

- Docker & Docker Compose
- Git

### Quick Setup (VPS / Linux Environment)

```bash
git clone https://github.com/yangyuan-zhen/PolyMusic.git
cd PolyMusic

# Run the automated build and deployment script
chmod +x deploy.sh
./deploy.sh
```

This script will automatically pull the latest codebase, clean up old non-compatible SQL databases, and boot up the FastAPI and Scraper containers.

### Access the Dashboard

Navigate to `http://<your-server-ip>:8001` (or localhost:8000 if running locally without docker).
The application will silently scrape and synchronize the latest data every 6 hours to keep the dashboard constantly updated.

## 🛠 Tech Stack

- **Backend/Scraping**: Python 3.10+, BeautifulSoup4, Requests
- **Database**: SQLite3
- **Web App**: FastAPI, Jinja2 Templates
- **Containerization**: Docker & Docker Compose

## Development

To run this application locally without Docker:

```bash
pip install -r requirements.txt
uvicorn web.main:app --host 0.0.0.0 --port 8000 --reload
# In a separate terminal, start the background listener:
python bot_listener.py
```
