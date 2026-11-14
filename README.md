# MoodSync Backend

REST API for [MoodSync](https://github.com/Piali-Singha/moodsync-frontend), an emotion-based music recommendation app. Built with FastAPI and PostgreSQL.

**Live API docs:** https://moodsync-backend-0tn9.onrender.com/docs
**Live app:** https://moodsync-frontend-omega.vercel.app
**Frontend repo & architecture overview:** https://github.com/Piali-Singha/moodsync-frontend

> Hosted on a free tier, so the first request after a period of inactivity can take up to a minute while the server wakes up.

## What it does

- Takes a mood (from the dial) or free text and returns song recommendations
- Detects emotion from text using a Hugging Face model (`j-hartmann/emotion-english-distilroberta-base`)
- Supports user accounts with JWT authentication (bcrypt-hashed passwords)
- Saves each mood check-in and returns a per-user history

## Endpoints

| Method | Path            | Auth     | Purpose                                    |
|--------|-----------------|----------|--------------------------------------------|
| POST   | `/register`     | No       | Create an account                          |
| POST   | `/login`        | No       | Get a JWT                                  |
| POST   | `/analyze-mood` | Optional | Get emotion and song recommendations       |
| GET    | `/mood-history` | Required | Last 50 check-ins for the logged-in user   |

Anonymous requests to `/analyze-mood` are allowed; they just aren't linked to a user.

## Tech stack

FastAPI, SQLAlchemy, PostgreSQL, PyJWT, bcrypt, Hugging Face Transformers

## Run locally

```bash
git clone https://github.com/Piali-Singha/moodsync-backend.git
cd moodsync-backend
python -m venv venv
venv\Scripts\activate                # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy.env.example .env                # macOS/Linux: cp .env.example .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to try the endpoints.

## Deployment note

The deployed version uses a lean `requirements.txt` without `torch`/`transformers` to fit the free tier's 512 MB RAM. The frontend always sends the selected emotion, so the model isn't needed there. Text-only analysis requires installing `transformers` and `torch` locally.
