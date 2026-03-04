# 🎵 PolyMusic: Quant Intelligence for Music Markets

PolyMusic is an independent quantitative analysis system designed to gain a decision-making edge in music prediction markets (e.g., PolyMarket). It aggregates real-time streaming data from Spotify, social signals from TikTok/YouTube, and industry events to provide deep market insights.

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![AI](https://img.shields.io/badge/AI-LLaMA%203.3%2070B-orange)

## 🚀 Key Features

- **Spotify Chart Scanner**: High-speed scraping of Global/US/UK Top 200 charts via kworb.net.
- **Quant Engines**:
  - **Accumulation Solver**: Calculates the "Stream Gap" required to flip rankings in weekly charts.
  - **Decay Controller**: Analyzes the half-life of trends to distinguish between "Spikes" and "Sustainable Hits."
- **AI Analytics (LLaMA 3.3 70B)**: Processes multi-source signals using a P0/P1/P2 framework to identify mispriced market opportunities.
- **Premium Dashboard**: A high-end web interface with Glassmorphism aesthetics for real-time monitoring.
- **Docker Ready**: One-click deployment to any VPS.

## 🛠️ Tech Stack

- **Backend**: Python 3.11, FastAPI
- **Database**: SQLite
- **AI Engine**: Groq SDK (LLaMA 3.3 70B)
- **Deployment**: Docker, Docker Compose
- **Design**: Vanilla CSS with Glassmorphism effects

## 📦 Quick Start

### 1. Prerequisite

- Python 3.11+ or Docker
- [Groq API Key](https://console.groq.com/)

### 2. Configuration

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_key_here
```

### 3. Running with Docker (Recommended)

```bash
docker-compose up -d --build
```

Access the dashboard at: `http://localhost:8000`

### 4. Running Locally

```bash
pip install -r requirements.txt
python bot_listener.py  # Run analysis engine
python web/main.py      # Start dashboard
```

## 📂 Project Structure

```text
PolyMusic/
├── src/
│   ├── data/            # Scrapers & DB logic
│   ├── analysis/        # Quant algorithms
│   └── ai/              # LLaMA prompt engine
├── web/                 # FastAPI dashboard & UI
├── data/                # Local SQLite storage
├── bot_listener.py      # Main pipeline entry
└── Dockerfile
```

## 📄 License

This project is licensed under the MIT License.
