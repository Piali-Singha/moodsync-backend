import os
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from app.songs import SONG_LIBRARY
import urllib.parse
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine, get_db
from app import models
from app.auth import hash_password, verify_password, create_access_token
from sqlalchemy.orm import Session
from app.auth import get_optional_user
from app.auth import get_optional_user, get_current_user

app = FastAPI()
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

_emotion_classifier = None


def get_emotion_classifier():
    """Load the Hugging Face model only when text-only analysis is needed."""
    global _emotion_classifier
    if _emotion_classifier is None:
        from transformers import pipeline

        _emotion_classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=1,
        )
    return _emotion_classifier


class MoodRequest(BaseModel):
    text: str
    emotion: str | None = None


class AuthRequest(BaseModel):
    email: str
    password: str


@app.post("/register")
def register(request: AuthRequest, db: Session = Depends(get_db)):
    email = request.email.strip().lower()
    if "@" not in email or len(email) < 5:
        raise HTTPException(status_code=400, detail="Enter a valid email address.")
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    if len(request.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password is too long (max 72 characters).")

    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = models.User(email=email, hashed_password=hash_password(request.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"token": create_access_token(user.id), "email": user.email}


@app.post("/login")
def login(request: AuthRequest, db: Session = Depends(get_db)):
    email = request.email.strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()

    if (
        not user
        or len(request.password.encode("utf-8")) > 72
        or not verify_password(request.password, user.hashed_password)
    ):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    return {"token": create_access_token(user.id), "email": user.email}


@app.post("/analyze-mood")
def analyze_mood(
    request: MoodRequest,
    db: Session = Depends(get_db),
    current_user: models.User | None = Depends(get_optional_user),   # NEW
):
    if request.emotion:
        detected_emotion = request.emotion
        confidence = 1.0
    else:
         result = get_emotion_classifier()(request.text)
         detected_emotion = result[0][0]["label"]
         confidence = result[0][0]["score"]

    songs = SONG_LIBRARY.get(detected_emotion, SONG_LIBRARY["neutral"])
    recommendations = []
    for song in songs:
        query = urllib.parse.quote(f"{song['title']} {song['artist']}")
        recommendations.append({
            "title": song["title"],
            "artist": song["artist"],
            "youtube_search_url": f"https://www.youtube.com/results?search_query={query}"
        })

    entry = models.MoodEntry(
        text=request.text,
        emotion=detected_emotion,
        confidence=confidence,
        user_id=current_user.id if current_user else None,           # NEW
    )
    db.add(entry)
    db.commit()

    return {
        "emotion": detected_emotion,
        "confidence": round(confidence, 3),
        "input_received": request.text,
        "recommendations": recommendations
    }
@app.get("/mood-history")
def mood_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    entries = (
        db.query(models.MoodEntry)
        .filter(models.MoodEntry.user_id == current_user.id)
        .order_by(models.MoodEntry.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": e.id,
            "text": e.text,
            "emotion": e.emotion,
            "confidence": round(e.confidence, 3),
            "created_at": e.created_at,
        }
        for e in entries
    ]