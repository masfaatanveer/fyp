# KFUEIT Agent Assist — Project Structure

```
kfueit-agent-assist/
│
├── SETUP.md                          ← Setup guide (start here)
├── PROJECT_STRUCTURE.md              ← This file
│
├── backend/
│   ├── manage.py
│   ├── requirements.txt              ← All Python dependencies
│   ├── .env.example                  ← Copy to .env and fill values
│   ├── celery.py                     ← Celery app config
│   │
│   ├── config/
│   │   ├── settings.py               ← Django settings (DB, OpenAI, Pinecone, n8n)
│   │   ├── urls.py                   ← Root URL routing
│   │   └── wsgi.py
│   │
│   └── apps/
│       └── agent/
│           ├── models.py             ← Student, CourseGrade, Attendance, Assignment, Fee, Complaint
│           ├── views.py              ← /api/agent/query/ and /api/agent/vapi/ endpoints
│           ├── urls.py               ← Agent URL patterns
│           ├── tasks.py              ← Celery task: daily KFUEIT website re-scrape
│           │
│           ├── management/
│           │   └── commands/
│           │       └── seed_dummy_data.py   ← python manage.py seed_dummy_data
│           │
│           └── services/
│               ├── tools.py          ← All LangGraph tools (DB queries + Pinecone + n8n webhooks)
│               ├── supervisor.py     ← LangGraph: Supervisor + 4 domain actors
│               └── scraper.py        ← Playwright: KFUEIT website scraper
│
├── frontend/
│   └── src/
│       └── components/
│           └── ChatWidget/
│               └── ChatWidget.tsx    ← React chat widget with voice call button
│
└── n8n/
    └── (export n8n workflow JSONs here for backup)
```

## Key Files to Understand

| File | What it does |
|---|---|
| `services/supervisor.py` | Core agent brain — Supervisor routes to 4 actors |
| `services/tools.py` | All tools the actors can call |
| `services/scraper.py` | Scrapes KFUEIT website → Pinecone |
| `models.py` | Dummy data schema for demo |
| `seed_dummy_data.py` | Creates 5 fake students with realistic data |
| `views.py` | Django API endpoints called by frontend + Vapi |
| `ChatWidget.tsx` | React widget — text chat + voice call button |
| `SETUP.md` | Step-by-step setup instructions |
