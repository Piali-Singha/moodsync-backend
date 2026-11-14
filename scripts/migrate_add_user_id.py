from sqlalchemy import text
from app.database import engine

with engine.begin() as conn:
    conn.execute(text(
        "ALTER TABLE mood_entries "
        "ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)"
    ))

print("Done: user_id column added to mood_entries")