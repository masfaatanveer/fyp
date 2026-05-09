# KFUEIT Agent Assist — CLAUDE.md
> FYP | Areeba Zameer + Masfa Tanveer | Supervisor: Dr. Badar ul Islam
> BS Artificial Intelligence, KFUEIT, Session 2022-26

---

## CRITICAL RULES (read before touching anything)

1. Models live in `backend/apps/agent/models.py` — 6 models: `StudentProfile`, `CourseEnrollment`, `AttendanceRecord`, `TranscriptCourse`, `SessionalMarks`, `Complaint`
2. Masfa's roll_no = `COSC221103029` — this is the primary demo student
3. `USE_DUMMY_DATA=True` in `.env` → uses PostgreSQL dummy data. Never set False unless LMS MySQL creds exist.
4. Always activate venv before running anything: `source backend/venv/bin/activate`
5. n8n webhooks WILL fail in demo (n8n not running) — this is EXPECTED, tools handle it gracefully
6. Pinecone key required for RAG tool — if missing, `admissions_actor` will fail silently (configured to return empty list gracefully)
7. Never run `makemigrations` without verifying models.py is correct first
8. LangGraph version in use: `langgraph>=0.2`, `langgraph-supervisor>=0.0.10` — if upgrading, verify `create_supervisor` + `create_react_agent` API hasn't changed

---

## Project Structure

```
kfueit-agent-assist/
├── CLAUDE.md                          ← this file (project root)
├── backend/
│   ├── venv/                          ← Python virtualenv (create if missing)
│   ├── .env                           ← API keys (create from .env.example)
│   ├── manage.py
│   ├── requirements.txt
│   ├── celeryapp.py                   ← Celery app config (renamed from celery.py to avoid circular import)
│   ├── config/
│   │   ├── settings.py                ← all settings + env vars
│   │   └── urls.py                    ← /admin/ + /api/agent/
│   └── apps/agent/
│       ├── models.py                  ← 6 models (StudentProfile etc.)
│       ├── views.py                   ← /api/agent/query/ + /api/agent/vapi/
│       ├── urls.py                    ← query/ + vapi/ + admin_logs/
│       ├── tasks.py                   ← Celery scrape task
│       ├── services/
│       │   ├── supervisor.py          ← LangGraph multi-agent system
│       │   ├── tools.py               ← all @tool functions
│       │   └── scraper.py             ← Playwright + Pinecone upsert
│       └── management/commands/
│           └── seed_dummy_data.py     ← seeds Masfa + 5 classmates
├── frontend/
│   └── src/components/ChatWidget/
│       └── ChatWidget.tsx             ← React widget (drop into any React app)
└── n8n/                               ← n8n workflow JSONs (future)
```

---

## Environment Setup (do once)

```bash
cd /home/masfatanveer/Documents/kfueit-agent-assist/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create PostgreSQL DB
psql -U postgres -c "CREATE DATABASE kfueit_agent;"

# Copy and fill .env
cp .env.example .env
# Fill: SECRET_KEY, OPENAI_API_KEY, PINECONE_API_KEY, DB_PASSWORD

# Run migrations
python manage.py migrate

# Seed dummy data
python manage.py seed_dummy_data

# Start server
python manage.py runserver
```

---

## Run & Test Commands

```bash
# Activate venv (always first)
source /home/masfatanveer/Documents/kfueit-agent-assist/backend/venv/bin/activate
cd /home/masfatanveer/Documents/kfueit-agent-assist/backend

# Start server
python manage.py runserver

# Test agent (attendance query)
curl -s -X POST http://localhost:8000/api/agent/query/ \
  -H "Content-Type: application/json" \
  -d '{"query":"meri attendance kitni hai", "roll_no":"COSC221103029"}' | python3 -m json.tool

# Test RAG (policy query)
curl -s -X POST http://localhost:8000/api/agent/query/ \
  -H "Content-Type: application/json" \
  -d '{"query":"what is kfueit attendance policy", "roll_no":"COSC221103029"}' | python3 -m json.tool

# Test admin logs
curl -s http://localhost:8000/api/agent/admin/logs/ | python3 -m json.tool

# Re-seed data
python manage.py seed_dummy_data

# Run scraper manually (requires OPENAI_API_KEY + PINECONE_API_KEY)
python manage.py shell -c "from apps.agent.services.scraper import scrape_and_index_all; scrape_and_index_all()"
```

---

## Models Reference

### StudentProfile
```
roll_no (unique), name, program, section, cgpa, credit_hours_req,
credit_hours_done, degree_status, phone, email
```
Demo students: COSC221103029 (Masfa), COSC221103026 (Areeba), COSC221103031, COSC221103045, COSC221103052, COSC221103038

### CourseEnrollment
```
student (FK→StudentProfile), course_code, course_name, credit_hours, section, semester
```
Masfa's current courses: COSC-4150, COSC-4130, MSCI-3111, COSC-4302

### AttendanceRecord
```
student (FK), course_code, course_name, date_time, status (P/A/L)
```
Has `attendance_summary` property → {present, total, percent}

### TranscriptCourse
```
student (FK), semester, course_code, course_name, grade, grade_point, credit_hours, gpa_earned
```
Masfa has real transcript: Fall 2022 → Spring 2023 → Fall 2023

### SessionalMarks
```
student (FK), course_code, course_name, assignment_marks, quiz_marks, mid_marks,
total_obtained, total_possible
```

### Complaint
```
student (FK), subject, description, status (open/in_progress/resolved),
created_at, resolved_at
```

### AgentLog
```
roll_no, query, response, actor_used, timestamp
```
Auto-written after every agent response. Powers admin dashboard.

---

## Agent Architecture

```
POST /api/agent/query/  →  views.agent_query()
                         ↓
                    run_agent(query, roll_no, thread_id)
                         ↓
              LangGraph Supervisor (GPT-4o-mini)
              routes to ONE of 4 actors:
                         ↓
    ┌──────────────────────────────────────────┐
    │ academics_actor  → get_student_info       │
    │                    get_student_attendance │
    │                    get_transcript         │
    │                    get_sessional_marks    │
    ├──────────────────────────────────────────┤
    │ lms_actor        → get_current_courses    │
    │                    get_sessional_marks    │
    ├──────────────────────────────────────────┤
    │ admin_actor      → log_complaint          │
    │                    send_email_to_teacher  │
    │                    escalate_to_hod        │
    ├──────────────────────────────────────────┤
    │ admissions_actor → search_university_knowledge │
    └──────────────────────────────────────────┘
                         ↓
              GPT-4o-mini generates response
                         ↓
              AgentLog saved to DB
                         ↓
              JSON response to client
```

---

## Phase Completion Status

- [x] Phase 0 — Environment: venv, packages, PostgreSQL, .env, migrations
- [x] Phase 1 — Models: 7 models (StudentProfile, CourseEnrollment, AttendanceRecord, TranscriptCourse, SessionalMarks, Complaint, AgentLog)
- [x] Phase 2 — Seed: Masfa real transcript (Fall 2022→Spring 2025) + 5 classmates
- [x] Phase 3 — Tools: 9 tools, correct models, graceful Pinecone fallback
- [x] Phase 4 — Supervisor: LangGraph verified, AgentLog auto-written, actor_used correct
- [x] Phase 5 — MVP: Agent live, all 4 actors routing correctly, curl tested
- [x] Phase 6 — RAG: Pinecone serverless index (multilingual-e5-large), scraper fixed (_id→id), 15 chunks indexed
- [x] Phase 7 — Admin Dashboard: React table at /#admin, stats cards, actor badges, filter by roll_no
- [x] Phase 8 — Frontend: Production React widget, markdown rendering, animated typing, quick prompts, Vapi hook
- [ ] Phase 9 — Voice: Vapi assistant ID needed (see below)
- [ ] Phase 10 — Memory: PostgresSaver checkpointer (LangGraph persistent memory)
- [ ] Phase 11 — LMS: Playwright login scraper for real student data

---

## What YOU Need to Provide (manual steps)

1. **`.env` file** — fill in these values:
   ```
   SECRET_KEY=any-random-50-char-string
   DB_PASSWORD=your-postgres-password
   OPENAI_API_KEY=sk-...
   PINECONE_API_KEY=pcsk_...
   PINECONE_INDEX_NAME=kfueit-agent
   ```
   Without OPENAI_API_KEY — agent won't work (LLM calls fail)
   Without PINECONE_API_KEY — only admissions_actor fails, rest works

2. **Pinecone index** ✅ Done — serverless, multilingual-e5-large, index: `kfueit-fyp`

3. **Frontend** ✅ Done — production React widget at `frontend/`
   - `http://localhost:5173` — chat widget
   - `http://localhost:5173/#admin` — admin dashboard

4. **Vapi voice** (Phase 9 — next):
   - Create assistant at vapi.ai → set server URL: `http://YOUR_IP:8000/api/agent/vapi/`
   - Add to `frontend/.env`: `VITE_VAPI_PUBLIC_KEY=...` and `VITE_VAPI_ASSISTANT_ID=...`
   - Add Vapi CDN to `frontend/index.html`: `<script src="https://cdn.vapi.ai/vapi.js"></script>`

---

## Known Issues & Fixes

| Issue | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'django'` | `source backend/venv/bin/activate` |
| `relation does not exist` | `python manage.py migrate` |
| `Student matching query does not exist` | `python manage.py seed_dummy_data` |
| n8n webhook timeout | Expected — complaint saved to DB, webhook skipped |
| Pinecone 404 / index not found | Create index in Pinecone dashboard first |
| `langgraph_supervisor` import error | Already on 0.0.31 — API is compatible, no action needed |
| `cannot import name 'Celery' from celery'` | celery.py was renamed to celeryapp.py — already fixed |
| Agent returns generic error | Check OPENAI_API_KEY is set in .env |

---

## LMS Hacking Plan (Phase 11 — future)

Goal: show Masfa's REAL LMS data instead of dummy data.

**Option A — Playwright scraper (recommended for FYP demo):**
```python
# scripts/lms_scraper.py
# 1. playwright login to lms.kfueit.edu.pk with student creds
# 2. scrape grades/attendance pages
# 3. store in StudentProfile + related models
# 4. set USE_DUMMY_DATA=True (data is now in our DB from real LMS)
```

**Option B — Direct MySQL (if you get DB creds):**
- Fill LMS_DB_* in .env
- Set USE_DUMMY_DATA=False
- tools.py already has production queries ready

**Widget injection into LMS:**
- Tampermonkey script on lms.kfueit.edu.pk
- Injects `<script src="http://your-ip:3000/widget.js"></script>`
- Widget appears on LMS pages, calls your backend

---

## Demo Script (FYP Presentation)

1. Open browser → LMS or your frontend
2. Click chat bubble (bottom-right)
3. Say: `"What is the attendance policy at KFUEIT?"` → RAG answer with citation
4. Say: `"Meri Routing & Switching attendance kitni hai?"` → real DB data
5. Say: `"I want to complain about missing marks in Reinforcement Learning"` → agent drafts email, asks confirmation
6. Confirm → complaint logged → show admin dashboard
7. Click phone icon → voice call demo (if Vapi configured)
