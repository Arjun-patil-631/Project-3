import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/smartassist.db")

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS conversations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            message TEXT,
            intent TEXT,
            created_at TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS feedback(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            rating TEXT,
            comment TEXT,
            created_at TEXT
        )""")
        conn.commit()

def add_message(session_id, role, message, intent=""):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO conversations(session_id,role,message,intent,created_at) VALUES(?,?,?,?,?)",
            (session_id, role, message, intent, datetime.utcnow().isoformat())
        )
        conn.commit()

def get_history(session_id, limit=8):
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT role,message,intent FROM conversations WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit)
        ).fetchall()
    return list(reversed(rows))

def add_feedback(session_id, rating, comment=""):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO feedback(session_id,rating,comment,created_at) VALUES(?,?,?,?)",
            (session_id, rating, comment, datetime.utcnow().isoformat())
        )
        conn.commit()

def all_conversations(limit=100):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            "SELECT session_id,role,message,intent,created_at FROM conversations ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()

def all_feedback(limit=100):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            """
            SELECT id, session_id, rating, comment, created_at
            FROM feedback
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
