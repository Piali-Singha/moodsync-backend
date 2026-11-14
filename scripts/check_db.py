from app.database import SessionLocal
from app import models

db = SessionLocal()
for e in db.query(models.MoodEntry).order_by(models.MoodEntry.id.desc()).limit(5):
    print(e.id, e.emotion, e.user_id)