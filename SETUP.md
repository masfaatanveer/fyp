# KFUEIT Agent Assist — Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (local install)
- Redis (local install)
- Docker (for n8n only)

---

## Step 1 — Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

---

## Step 2 — Environment Variables

```bash
cp .env.example .env
# Edit .env and fill in:
# - SECRET_KEY (any random string)
# - DB_NAME, DB_USER, DB_PASSWORD (your PostgreSQL credentials)
# - OPENAI_API_KEY (from platform.openai.com)
# - PINECONE_API_KEY (from pinecone.io)
# - PINECONE_INDEX_NAME (create index named: kfueit-agent, dimension: 1536)
# Keep USE_DUMMY_DATA=True for demo
```

---

## Step 3 — Database Setup

```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE kfueit_agent;"

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Seed dummy student data
python manage.py seed_dummy_data
```

---

## Step 4 — Pinecone Index

Go to https://pinecone.io → Create index:
- Name: `kfueit-agent`
- Dimensions: `1536`
- Metric: `cosine`
- Cloud: AWS, Region: us-east-1 (free tier)

Then scrape KFUEIT website (first time only):
```bash
python manage.py shell
>>> from apps.agent.services.scraper import scrape_and_index_all
>>> scrape_and_index_all()
>>> exit()
```

---

## Step 5 — Start n8n (Docker)

```bash
docker run -it --rm -p 5678:5678 n8nio/n8n
```

Open http://localhost:5678 → Create 3 webhooks:
1. POST `/webhook/send-email` → Gmail node
2. POST `/webhook/log-complaint` → just respond 200 (or connect to Sheets)
3. POST `/webhook/escalate` → Gmail node (to HOD email)

---

## Step 6 — Start Redis

```bash
# Linux
sudo service redis start

# Or with Docker
docker run -d -p 6379:6379 redis:alpine
```

---

## Step 7 — Run Everything

Open 3 terminals:

**Terminal 1 — Django:**
```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

**Terminal 2 — Celery (optional for demo):**
```bash
cd backend
source venv/bin/activate
celery -A celery worker --loglevel=info
```

**Terminal 3 — Frontend (optional):**
```bash
cd frontend
npm install
npm run dev
```

---

## Step 8 — Test the Agent

```bash
curl -X POST http://localhost:8000/api/agent/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Meri attendance kitni hai?", "roll_no": "COSC221103029"}'
```

Expected response:
```json
{
  "response": "Masfa, aapki course-wise attendance yeh hai:\n\n- Deep Learning: 28/35 (80%) — OK\n- NLP: 18/30 (60%) — SHORT ⚠️...",
  "session_id": "..."
}
```

---

## Demo Roll Numbers (Seeded Dummy Data)

| Roll No | Name |
|---|---|
| COSC221103029 | Masfa Tanveer |
| COSC221103026 | Areeba Zameer |
| COSC221103010 | Ali Hassan |
| COSC221103015 | Fatima Noor |
| COSC221103020 | Usman Tariq |

---

## Production Upgrade (After Demo)

To switch from dummy data to real LMS MySQL:
1. Set `USE_DUMMY_DATA=False` in `.env`
2. Fill in `LMS_DB_*` credentials in `.env`
3. Restart Django — tools will automatically use MySQL queries

No code changes needed — tools.py handles both paths.
