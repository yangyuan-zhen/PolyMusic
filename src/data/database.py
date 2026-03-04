import sqlite3
import os

DB_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../data/polymusic.db'))

def init_db():
    """
    Initializes the SQLite database with necessary tables.
    """
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Spotify Charts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS spotify_charts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        region TEXT,
        position INTEGER,
        track_name TEXT,
        artist TEXT,
        streams INTEGER,
        UNIQUE(date, region, track_name, artist)
    )
    ''')
    
    # MAE / Prediction Error table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prediction_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        market_name TEXT,
        polymarket_price REAL,
        actual_outcome REAL,
        mae REAL
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
