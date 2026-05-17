import sqlite3

def init_db():
    conn = sqlite3.connect("matcher.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS match_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        resume_name TEXT,
        job_title TEXT,
        company TEXT,
        match_percent REAL,
        matched_skills TEXT,
        missing_skills TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print("✅ Database Ready: match_history table active")
