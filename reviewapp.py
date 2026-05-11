import sqlite3
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta

app = FastAPI()

DB = "news.db"
LOCK_TIMEOUT_MINUTES = 10


# =========================
# Database Migration
# =========================

conn = sqlite3.connect(DB)
cursor = conn.cursor()

try:
    cursor.execute("""
        ALTER TABLE news
        ADD COLUMN reviewed INTEGER DEFAULT 0
    """)
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("""
        ALTER TABLE news
        ADD COLUMN locked_by TEXT
    """)
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("""
        ALTER TABLE news
        ADD COLUMN locked_at TEXT
    """)
except sqlite3.OperationalError:
    pass

conn.commit()
conn.close()


# =========================
# Request Model
# =========================

class ReviewRequest(BaseModel):
    id: int
    category: str
    reviewer: str


# =========================
# GET ARTICLE (WITH TIMEOUT LOCK)
# =========================

@app.get("/news/review")
def get_news(reviewer: str):

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # 🔥 أهم تعديل: ناخد المقال حتى لو lock قديم أو فاضي
    cursor.execute("""
        SELECT id, title, category, confidence
        FROM news
        WHERE confidence < 0.65
        AND reviewed = 0
        AND (
            locked_by IS NULL
            OR datetime(locked_at) < datetime('now', ?)
        )
        ORDER BY created_at DESC
        LIMIT 1
    """, (f"-{LOCK_TIMEOUT_MINUTES} minutes",))

    row = cursor.fetchone()

    if not row:
        conn.close()
        return {"message": "No articles left"}

    news_id = row[0]

    # 🔥 Lock جديد
    cursor.execute("""
        UPDATE news
        SET locked_by = ?,
            locked_at = ?
        WHERE id = ?
    """, (
        reviewer,
        datetime.utcnow().isoformat(),
        news_id
    ))

    conn.commit()
    conn.close()

    return {
        "id": row[0],
        "title": row[1],
        "predicted": row[2],
        "confidence": row[3]
    }


# =========================
# SUBMIT REVIEW
# =========================

@app.post("/news/review")
def review_news(data: ReviewRequest):

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE news
        SET category = ?,
            reviewed = 1,
            locked_by = NULL,
            locked_at = NULL
        WHERE id = ?
    """, (
        data.category,
        data.id
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Review saved"
    }