# KFUEIT Agent Assist — Skills & Orchestration
> Production implementation guide for every phase.
> Read this FIRST before touching any code. Each skill maps to a phase.

---

## How to use this file
Each skill below has:
- **State** — current status
- **Files** — exact paths to touch
- **Steps** — production-level implementation steps
- **Test** — how to verify it works

---

## Skill 01 — Environment & Infrastructure
**State:** ✅ Complete

**Files:**
- `backend/venv/` — Python 3.12 virtualenv
- `backend/.env` — all secrets (never commit)
- `backend/requirements.txt` — pinned dependencies
- `backend/celeryapp.py` — Celery app (NOT celery.py — circular import)
- `backend/config/settings.py` — all Django settings

**Key facts:**
- PostgreSQL DB: `kfueit_agent`, user: `postgres`, password in `.env`
- `USE_DUMMY_DATA=True` always unless real LMS MySQL creds exist
- `OPENAI_LLM_MODEL` defaults to `gpt-4o-mini` if not in `.env`
- Pinecone index: `kfueit-fyp`, serverless AWS us-east-1, `multilingual-e5-large`

---

## Skill 02 — Django Models
**State:** ✅ Complete

**Files:** `backend/apps/agent/models.py`

**Models (7 total):**
```
StudentProfile      → roll_no(unique), name, program, section, cgpa, credit_hours_req/done, degree_status
CourseEnrollment    → student FK, course_code, course_name, credit_hours, section, semester
AttendanceRecord    → student FK, course_code, date_time, status(P/A/L) + attendance_summary property
TranscriptCourse    → student FK, semester, course_code, grade, grade_point, credit_hours, gpa_earned
SessionalMarks      → student FK, course_code, assignment_marks, quiz_marks, mid_marks, total_obtained/possible
Complaint           → student FK, subject, description, status(open/in_progress/resolved)
AgentLog            → roll_no, session_id, query, response, actor_used, created_at
```

**Rules:**
- Never rename these models — tools.py references them directly
- `AttendanceRecord.attendance_summary` is a @property, not a DB field
- AgentLog is auto-written by `run_agent()` after every query

---

## Skill 03 — Seed Data
**State:** ✅ Complete

**Files:** `backend/apps/agent/management/commands/seed_dummy_data.py`

**Run:** `python manage.py seed_dummy_data`

**Data:**
- Masfa (COSC221103029): real transcript Fall 2022→Spring 2025, CGPA 3.15, 4 current courses
- 5 classmates: COSC221103026, 031, 045, 052, 038
- 12 attendance records per course per student (~83% attendance)
- Sessional marks generated in realistic ranges

---

## Skill 04 — LangGraph Tools
**State:** ✅ Complete

**Files:** `backend/apps/agent/services/tools.py`

**9 tools:**
```
get_student_info        → academics_actor — profile, CGPA, program
get_current_courses     → lms_actor — current semester enrollments
get_student_attendance  → academics_actor — course-wise present/absent/percent
get_transcript          → academics_actor — full historical grades
get_sessional_marks     → academics_actor + lms_actor — assignment/quiz/mid
log_complaint           → admin_actor — saves Complaint + n8n webhook
send_email_to_teacher   → admin_actor — n8n webhook (fails gracefully if offline)
escalate_to_hod         → admin_actor — n8n webhook
search_university_knowledge → admissions_actor — Pinecone RAG search
```

**Pinecone RAG flow:**
- Searches `student_{roll_no}` namespace first, falls back to `kfueit_public`
- Uses `pinecone_api.py` SDK (NOT raw HTTP) — `index.search_records()`
- Graceful fallback if Pinecone keys missing

---

## Skill 05 — LangGraph Supervisor
**State:** ✅ Complete

**Files:** `backend/apps/agent/services/supervisor.py`

**Architecture:**
```
run_agent(query, roll_no, thread_id)
    → LangGraph Supervisor (gpt-4o-mini)
    → routes to ONE actor
    → actor calls tools
    → gpt-4o-mini generates response
    → AgentLog.objects.create(...)
    → returns string
```

**Routing:**
- `academics_actor` — attendance, transcript, CGPA, sessional marks
- `lms_actor` — current courses, marks breakdown
- `admin_actor` — complaints, emails, HOD escalation
- `admissions_actor` — university policies, admission info (RAG)

**Important:** `_supervisor_graph` is a singleton — built once on first request, reused.

---

## Skill 06 — Pinecone RAG
**State:** ✅ Complete

**Files:**
- `backend/apps/agent/services/scraper.py` — Playwright scraper
- `backend/apps/agent/services/pinecone_api.py` — SDK wrapper
- `backend/apps/agent/services/pinecone_utils.py` — namespace utilities

**Run scraper:**
```bash
source venv/bin/activate
python manage.py shell -c "from apps.agent.services.scraper import scrape_and_index_all; scrape_and_index_all()"
```

**Critical:** Records use `id` (NOT `_id`) — Pinecone integrated inference API requires this.

**Pinecone SDK:** Uses `pinecone` package (NOT `pinecone-client`). `index.upsert_records()` for upload, `index.search_records()` for search.

**Namespaces:**
- `kfueit_public` — scraped KFUEIT website content
- `student_{roll_no}` — per-student data (future use)

---

## Skill 07 — Admin Dashboard
**State:** ✅ Complete

**Backend:** `GET /api/agent/admin/logs/?roll_no=...&limit=50`
**Frontend:** `http://localhost:5173/#admin`

**Files:**
- `backend/apps/agent/views.py` — `admin_logs()` view
- `frontend/src/components/AdminDashboard/AdminDashboard.tsx`

**Features:** Stats cards (total, unique students, per-actor), filterable table, actor color badges, time-ago timestamps

---

## Skill 08 — Production Frontend
**State:** ✅ Complete

**Files:**
- `frontend/src/components/ChatWidget/ChatWidget.tsx`
- `frontend/src/styles.css`
- `frontend/src/App.tsx`

**Run:** `cd frontend && npm run dev` → `http://localhost:5173`

**Features:**
- Floating FAB (closed by default)
- Slide-up animation on open
- Animated 3-dot typing indicator
- Markdown rendering (react-markdown) for bold/lists in agent responses
- Timestamps on messages
- Quick prompts (disappear after first interaction)
- Online status indicator
- Voice call button (wired for Vapi)

**Admin page:** `http://localhost:5173/#admin`

---

## Skill 09 — Voice (Vapi)
**State:** 🔲 Pending

**What's needed from user:**
1. Go to vapi.ai → Create assistant
2. Set server URL: `http://YOUR_IP:8000/api/agent/vapi/`
3. Add to `frontend/.env`:
   ```
   VITE_VAPI_PUBLIC_KEY=your_public_key
   VITE_VAPI_ASSISTANT_ID=your_assistant_id
   ```
4. Add to `frontend/index.html` before `</body>`:
   ```html
   <script>
     (function(d,t){var g=document.createElement(t),s=d.getElementsByTagName(t)[0];g.src="https://cdn.vapi.ai/vapi.js";g.onload=function(){window.__vapi=new window.Vapi("YOUR_PUBLIC_KEY");};s.parentNode.insertBefore(g,s);})(document,"script");
   </script>
   ```

**Backend already handles Vapi:**
- `POST /api/agent/vapi/` — receives transcript, runs agent, returns response
- Roll no passed via call metadata

---

## Skill 10 — Conversation Memory (PostgresSaver)
**State:** 🔲 Pending

**What to implement:**
```python
# In supervisor.py _build_supervisor():
from langgraph.checkpoint.postgres import PostgresSaver

conn_string = f"postgresql://postgres:{settings.DB_PASSWORD}@localhost:5432/kfueit_agent"
checkpointer = PostgresSaver.from_conn_string(conn_string)
return supervisor.compile(checkpointer=checkpointer)
```

**Effect:** Agent remembers previous messages within a session (thread_id = student session).

**Warning:** Run `checkpointer.setup()` once to create checkpoint tables.

---

## Skill 11 — Real LMS Data
**State:** 🔲 Future (Post-FYP or demo enhancement)

**Option A — Playwright scraper (recommended):**
```python
# scripts/lms_scraper.py
# 1. Playwright login to lms.kfueit.edu.pk
# 2. Navigate to grades/attendance pages
# 3. Parse and store into StudentProfile + related models
# 4. USE_DUMMY_DATA stays True (data now real, stored in our DB)
```

**Option B — Direct MySQL:**
- Fill `LMS_DB_*` in `.env`
- Set `USE_DUMMY_DATA=False`
- tools.py already has production MySQL queries

**Widget injection into LMS (Tampermonkey):**
```js
// Inject into lms.kfueit.edu.pk pages
const s = document.createElement("script");
s.src = "http://YOUR_IP:5173/assets/index.js";
document.body.appendChild(s);
```

---

## Quick Commands Reference

```bash
# ── Backend ──────────────────────────────────────────────────────────────────
cd /home/masfatanveer/Documents/kfueit-agent-assist/backend
source venv/bin/activate

python manage.py runserver                    # start server
python manage.py migrate                      # apply migrations
python manage.py seed_dummy_data              # re-seed all 6 students
python manage.py makemigrations agent         # only after verifying models.py

# ── Test queries ─────────────────────────────────────────────────────────────
curl -s -X POST http://localhost:8000/api/agent/query/ \
  -H "Content-Type: application/json" \
  -d '{"query":"meri attendance kitni hai","roll_no":"COSC221103029"}' | python3 -m json.tool

curl -s http://localhost:8000/api/agent/admin/logs/ | python3 -m json.tool

# ── Scraper ───────────────────────────────────────────────────────────────────
python manage.py shell -c "from apps.agent.services.scraper import scrape_and_index_all; scrape_and_index_all()"

# ── Frontend ──────────────────────────────────────────────────────────────────
cd /home/masfatanveer/Documents/kfueit-agent-assist/frontend
npm run dev      # http://localhost:5173
npm run build    # production build
```

---

## Demo Script (FYP Presentation)

1. Open `http://localhost:5173` — show hero page
2. Click FAB (bottom-right) → chat opens with animation
3. Click quick prompt: **"Meri attendance kitni hai?"** → academics_actor responds with real data
4. Type: **"Mera transcript dikhao"** → formatted table with all semesters
5. Type: **"KFUEIT ki attendance policy kya hai?"** → admissions_actor with RAG result
6. Type: **"I want to complain about missing marks in Reinforcement Learning"** → admin_actor drafts email, asks confirmation
7. Open `http://localhost:5173/#admin` → show admin dashboard with all 6 queries logged
8. (Optional) Click phone icon → Vapi voice call demo

---

## Known Issues & Fixes

| Issue | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'django'` | `source backend/venv/bin/activate` |
| `relation does not exist` | `python manage.py migrate` |
| Pinecone upsert 400 error | Use `id` not `_id` in records |
| `pinecone-client` import error | `pip uninstall pinecone-client && pip install pinecone` |
| `celery` circular import | File must be `celeryapp.py` not `celery.py` |
| n8n webhook timeout | Expected in demo — complaint saves to DB, webhook skipped gracefully |
| Agent returns generic error | Check `OPENAI_API_KEY` in `.env` |
| RAG returns no results | Run scraper first: `scrape_and_index_all()` |
| `actor_used` shows "supervisor" | Fixed — scans all messages for actor name |
