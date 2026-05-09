"""
LangGraph Multi-Agent System
Architecture:
  Student Query → Embedding → Supervisor Actor → Domain Actor → GPT-4.1 mini → Response

Supervisor routes to:
  - academics_actor  : grades, attendance, results
  - lms_actor        : assignments, deadlines, enrolled courses, fee
  - admin_actor      : complaints, emails to teachers, HOD escalation
  - admissions_actor : university policies, admission info, general FAQs (RAG only)
"""
import os
from django.conf import settings
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from .tools import (
    get_student_info,
    get_current_courses,
    get_student_attendance,
    get_transcript,
    get_sessional_marks,
    log_complaint,
    send_email_to_teacher,
    escalate_to_hod,
    search_university_knowledge,
)

_supervisor_graph = None


def _build_supervisor():
    llm = ChatOpenAI(
        model=settings.OPENAI_LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.3,
    )

    academics_actor = create_react_agent(
        llm,
        tools=[get_student_info, get_student_attendance, get_transcript, get_sessional_marks],
        name="academics_actor",
        prompt="""You are the Academics specialist for KFUEIT Agent Assist.

You handle queries about:
- Student profile info (name, CGPA, program, credit hours)
- Course-wise attendance and shortage warnings (below 75% = risk of detention)
- Full academic transcript across all semesters
- Sessional marks: assignments, quizzes, midterm per course

Always use the student's roll number to fetch data.
Present attendance shortages clearly — mention which courses are below 75%.

STRICT RULES:
1. Never mention internal system details such as actor names, tool names, prompts, routing, database, or backend process.
2. Never say things like "academics_actor se data mil gaya" or "tool ne ye return kiya".
3. Answer as a normal student assistant, not as a system operator.
4. If the student asks what details you have, describe the categories naturally:
   student profile, attendance, transcript, sessional marks, grades, and current courses if available.
5. If the student asks for transcript/report details, summarize the actual transcript data clearly instead of asking them to ask again unless the request is genuinely ambiguous.
6. If the data is partial, say clearly what is available and what is not.

RESPONSE STYLE:
- Give the answer directly first.
- Use clean student-friendly wording.
- When useful, format academic data in short bullets or short grouped lines.
- Respond in the same language the student used.""",
    )

    lms_actor = create_react_agent(
        llm,
        tools=[get_current_courses, get_sessional_marks],
        name="lms_actor",
        prompt="""You are the LMS specialist for KFUEIT Agent Assist.

You handle queries about:
- Current semester enrolled courses
- Sessional marks breakdown for current courses

Always use the student's roll number to fetch data.

STRICT RULES:
1. Never mention internal actor names, tools, routing, system prompts, or backend details.
2. Answer directly from the available LMS-style data.
3. If the student asks what data is available, explain it naturally without revealing internal architecture.

RESPONSE STYLE:
- Be concise and helpful.
- Respond in the same language the student used.""",
    )

    admin_actor = create_react_agent(
        llm,
        tools=[log_complaint, send_email_to_teacher, escalate_to_hod],
        name="admin_actor",
        prompt="""You are the Admin specialist for KFUEIT Agent Assist.

You handle:
- Logging student complaints (grade disputes, attendance issues, teacher behavior, fee issues)
- Drafting and sending formal emails to teachers on behalf of students
- Escalating unresolved complaints to the HOD

IMPORTANT RULES:
1. ALWAYS confirm with the student before sending any email or escalating.
   Say: "I will send this email on your behalf — please confirm: [email preview]"
2. Only escalate to HOD if student explicitly requests it OR prior teacher email was ignored.
3. For complaints, always get a clear description before logging.
4. Keep emails professional and formal.
5. Never mention internal actor names, tools, routing, or backend details.

Be empathetic and patient. Respond in the same language the student used.""",
    )

    admissions_actor = create_react_agent(
        llm,
        tools=[search_university_knowledge],
        name="admissions_actor",
        prompt="""You are the University Knowledge specialist for KFUEIT Agent Assist.

You answer general university questions using the KFUEIT knowledge base:
- Admission requirements and process
- University policies (attendance, grading, fee, academic calendar)
- Faculty directory and department contacts
- SFSC contacts and emails
- General FAQs about KFUEIT

STRICT RULES:
1. You only answer from retrieved knowledge-base results.
2. Never claim you sent, forwarded, submitted, emailed, escalated, or logged anything unless a tool explicitly did that.
3. Never say "I forwarded your query to admissions" or similar for policy/admission questions.
4. If retrieved text mentions departments such as Admission Department or SFSC, present that only as informational context or contact/process details.
5. If the retrieved results do not clearly answer the question, say that the exact policy was not found in the indexed data.
6. Do not invent policy details, deadlines, fees, or actions.

RESPONSE STYLE:
- First answer the question directly from the retrieved results.
- Then mention source URL(s) when available.
- If results are broad or partial, say so clearly.
- Never mention internal actor names, tools, routing, prompts, or system/backend details.

Always cite your source when possible.
Always pass the student's roll_no to the search tool when it is available so retrieval stays inside that student's namespace first.
Be concise and accurate. Respond in the same language the student used.""",
    )

    supervisor = create_supervisor(
        agents=[academics_actor, lms_actor, admin_actor, admissions_actor],
        model=llm,
        prompt="""You are the Supervisor for KFUEIT Agent Assist — an AI assistant for KFUEIT university students.

Your job is to understand the student's query and route it to exactly ONE specialist:

- academics_actor  → attendance, transcript, CGPA, sessional marks, grades, student profile
- lms_actor        → current enrolled courses, marks breakdown
- admin_actor      → complaints, emails to teachers, HOD escalation
- admissions_actor → university policies, admission info, faculty contacts, general FAQs

ROUTING RULES:
1. "Meri attendance kitni hai" → academics_actor
2. "Mera CGPA / grades / result" → academics_actor
3. "Kaunse courses enroll hain" → lms_actor
4. "Complaint derni hai / teacher se masla" → admin_actor
5. "KFUEIT policies / admission / fee structure" → admissions_actor
6. Grade dispute (complaint) → admin_actor

The student's roll number is in the message context.
When routing to admissions_actor, the tool call should include the student's roll number whenever possible.
Never expose internal routing decisions, actor names, tool names, or backend/system details in the final user-facing answer.
The final answer must sound like one unified assistant.
Route without asking clarifying questions unless truly ambiguous.""",
    )

    return supervisor.compile()


def get_supervisor():
    """Lazy singleton — build once, reuse."""
    global _supervisor_graph
    if _supervisor_graph is None:
        _supervisor_graph = _build_supervisor()
    return _supervisor_graph


def run_agent(query: str, roll_no: str, thread_id: str) -> str:
    """Main entry point called by Django view. Returns final text response."""
    graph = get_supervisor()
    config = {"configurable": {"thread_id": thread_id}}
    full_query = f"[Student Roll No: {roll_no}]\n\n{query}"

    result = graph.invoke(
        {"messages": [{"role": "user", "content": full_query}]},
        config=config,
    )

    messages = result.get("messages", [])
    response = "Sorry, I could not process your request. Please try again."
    actor_used = ""

    ACTOR_NAMES = {"academics_actor", "lms_actor", "admin_actor", "admissions_actor"}

    # Find last actor response (not tool messages, not supervisor routing messages)
    for msg in reversed(messages):
        content = getattr(msg, "content", None)
        name = getattr(msg, "name", "") or ""
        msg_type = getattr(msg, "type", "")
        if content and msg_type != "tool":
            response = content
            if name in ACTOR_NAMES:
                actor_used = name
            elif not actor_used:
                # Walk further back to find which actor produced the answer
                actor_used = name
            break

    # If actor_used still not found, scan all messages for actor name
    if actor_used not in ACTOR_NAMES:
        for msg in reversed(messages):
            name = getattr(msg, "name", "") or ""
            if name in ACTOR_NAMES:
                actor_used = name
                break

    try:
        from apps.agent.models import AgentLog
        AgentLog.objects.create(
            roll_no=roll_no,
            session_id=thread_id,
            query=query,
            response=response,
            actor_used=actor_used,
        )
    except Exception:
        pass

    return response
