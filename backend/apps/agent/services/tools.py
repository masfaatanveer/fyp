"""
LangGraph tools — called by domain actors.
USE_DUMMY_DATA=True  → queries PostgreSQL (demo)
USE_DUMMY_DATA=False → queries LMS MySQL (production)
"""
import requests
from django.conf import settings
from langchain_core.tools import tool

from .pinecone_api import search_text_records
from .pinecone_utils import extract_roll_no_from_text, get_query_namespaces


def _get_student(roll_no: str):
    from apps.agent.models import StudentProfile
    try:
        return StudentProfile.objects.get(roll_no=roll_no), None
    except StudentProfile.DoesNotExist:
        return None, {"error": f"Student with roll number {roll_no} not found."}


# ── Academics Tools ───────────────────────────────────────────────────────────

@tool
def get_student_info(roll_no: str) -> dict:
    """Fetch basic student profile: name, program, section, CGPA, credit hours, degree status."""
    if settings.USE_DUMMY_DATA:
        student, err = _get_student(roll_no)
        if err:
            return err
        return {
            "roll_no": student.roll_no,
            "name": student.name,
            "program": student.program,
            "section": student.section,
            "cgpa": student.cgpa,
            "credit_hours_done": student.credit_hours_done,
            "credit_hours_req": student.credit_hours_req,
            "degree_status": student.degree_status,
            "email": student.email,
            "phone": student.phone,
        }
    else:
        from django.db import connections
        with connections["lms"].cursor() as cursor:
            cursor.execute(
                "SELECT name, program, section, cgpa, credit_hours_done, credit_hours_req, degree_status, email, phone FROM students WHERE roll_no = %s",
                [roll_no],
            )
            row = cursor.fetchone()
            if not row:
                return {"error": f"Student {roll_no} not found."}
            cols = ["name", "program", "section", "cgpa", "credit_hours_done", "credit_hours_req", "degree_status", "email", "phone"]
            return {"roll_no": roll_no, **dict(zip(cols, row))}


@tool
def get_current_courses(roll_no: str) -> list[dict]:
    """Fetch courses the student is currently enrolled in (current semester)."""
    if settings.USE_DUMMY_DATA:
        from apps.agent.models import CourseEnrollment
        student, err = _get_student(roll_no)
        if err:
            return [err]
        enrollments = CourseEnrollment.objects.filter(student=student)
        return [
            {
                "course_code": e.course_code,
                "course_name": e.course_name,
                "credit_hours": e.credit_hours,
                "section": e.section,
                "semester": e.semester,
            }
            for e in enrollments
        ]
    else:
        from django.db import connections
        with connections["lms"].cursor() as cursor:
            cursor.execute(
                "SELECT course_code, course_name, credit_hours, section, semester FROM enrollments WHERE roll_no = %s",
                [roll_no],
            )
            rows = cursor.fetchall()
            return [{"course_code": r[0], "course_name": r[1], "credit_hours": r[2], "section": r[3], "semester": r[4]} for r in rows]


@tool
def get_student_attendance(roll_no: str) -> list[dict]:
    """Fetch course-wise attendance summary for a student."""
    if settings.USE_DUMMY_DATA:
        from apps.agent.models import AttendanceRecord
        student, err = _get_student(roll_no)
        if err:
            return [err]

        course_codes = AttendanceRecord.objects.filter(student=student).values_list("course_code", flat=True).distinct()
        result = []
        for code in course_codes:
            records = AttendanceRecord.objects.filter(student=student, course_code=code)
            total = records.count()
            present = records.filter(status="P").count()
            absent = records.filter(status="A").count()
            leave = records.filter(status="L").count()
            percent = round(present / total * 100, 1) if total > 0 else 0
            course_name = records.first().course_name
            result.append({
                "course_code": code,
                "course_name": course_name,
                "present": present,
                "absent": absent,
                "leave": leave,
                "total": total,
                "percentage": percent,
                "status": "OK" if percent >= 75 else "SHORT — risk of detention",
            })
        return result
    else:
        from django.db import connections
        with connections["lms"].cursor() as cursor:
            cursor.execute(
                "SELECT course_code, course_name, present_count, absent_count, total_classes FROM attendance WHERE roll_no = %s",
                [roll_no],
            )
            rows = cursor.fetchall()
            result = []
            for r in rows:
                pct = round(r[2] / r[4] * 100, 1) if r[4] else 0
                result.append({
                    "course_code": r[0],
                    "course_name": r[1],
                    "present": r[2],
                    "absent": r[3],
                    "total": r[4],
                    "percentage": pct,
                    "status": "OK" if pct >= 75 else "SHORT — risk of detention",
                })
            return result


@tool
def get_transcript(roll_no: str) -> list[dict]:
    """Fetch full academic transcript (all past semesters) for a student."""
    if settings.USE_DUMMY_DATA:
        from apps.agent.models import TranscriptCourse
        student, err = _get_student(roll_no)
        if err:
            return [err]
        courses = TranscriptCourse.objects.filter(student=student).order_by("semester")
        return [
            {
                "semester": tc.semester,
                "course_code": tc.course_code,
                "course_name": tc.course_name,
                "grade": tc.grade,
                "grade_point": tc.grade_point,
                "credit_hours": tc.credit_hours,
                "gpa_earned": tc.gpa_earned,
            }
            for tc in courses
        ]
    else:
        from django.db import connections
        with connections["lms"].cursor() as cursor:
            cursor.execute(
                "SELECT semester, course_code, course_name, grade, grade_point, credit_hours, gpa_earned FROM transcript WHERE roll_no = %s ORDER BY semester",
                [roll_no],
            )
            rows = cursor.fetchall()
            cols = ["semester", "course_code", "course_name", "grade", "grade_point", "credit_hours", "gpa_earned"]
            return [dict(zip(cols, r)) for r in rows]


@tool
def get_sessional_marks(roll_no: str) -> list[dict]:
    """Fetch sessional marks (assignments, quizzes, midterm) for current semester courses."""
    if settings.USE_DUMMY_DATA:
        from apps.agent.models import SessionalMarks
        student, err = _get_student(roll_no)
        if err:
            return [err]
        marks = SessionalMarks.objects.filter(student=student)
        return [
            {
                "course_code": m.course_code,
                "course_name": m.course_name,
                "assignment_marks": m.assignment_marks,
                "quiz_marks": m.quiz_marks,
                "mid_marks": m.mid_marks,
                "total_obtained": m.total_obtained,
                "total_possible": m.total_possible,
                "percentage": round(m.total_obtained / m.total_possible * 100, 1) if m.total_possible else 0,
            }
            for m in marks
        ]
    else:
        from django.db import connections
        with connections["lms"].cursor() as cursor:
            cursor.execute(
                "SELECT course_code, course_name, assignment_marks, quiz_marks, mid_marks, total_obtained, total_possible FROM sessional_marks WHERE roll_no = %s",
                [roll_no],
            )
            rows = cursor.fetchall()
            cols = ["course_code", "course_name", "assignment_marks", "quiz_marks", "mid_marks", "total_obtained", "total_possible"]
            return [dict(zip(cols, r)) for r in rows]


# ── Admin Tools (n8n webhooks) ────────────────────────────────────────────────

@tool
def log_complaint(roll_no: str, subject: str, description: str) -> dict:
    """
    Log a student complaint. subject should briefly describe the issue.
    Saves to DB and notifies n8n workflow.
    """
    from apps.agent.models import Complaint
    student, err = _get_student(roll_no)
    if err:
        return err

    complaint = Complaint.objects.create(
        student=student,
        subject=subject,
        description=description,
        status="open",
    )

    try:
        requests.post(
            settings.N8N_WEBHOOK_LOG_COMPLAINT,
            json={
                "complaint_id": complaint.id,
                "roll_no": roll_no,
                "student_name": student.name,
                "subject": subject,
                "description": description,
                "timestamp": str(complaint.created_at),
            },
            timeout=5,
        )
    except requests.RequestException:
        pass

    return {
        "success": True,
        "complaint_id": complaint.id,
        "message": f"Complaint logged (ID #{complaint.id}). Status: Open.",
    }


@tool
def send_email_to_teacher(roll_no: str, teacher_email: str, subject: str, body: str) -> dict:
    """
    Send a formal email to a teacher on behalf of the student via n8n.
    Always confirm intent with the student before calling this tool.
    """
    student, err = _get_student(roll_no)
    if err:
        return err

    try:
        requests.post(
            settings.N8N_WEBHOOK_SEND_EMAIL,
            json={
                "to": teacher_email,
                "subject": subject,
                "body": body,
                "from_name": student.name,
                "from_roll": roll_no,
            },
            timeout=5,
        )
        return {"success": True, "message": f"Email sent to {teacher_email}."}
    except requests.RequestException as e:
        return {"error": f"Failed to send email: {str(e)}"}


@tool
def escalate_to_hod(complaint_id: int, reason: str) -> dict:
    """
    Escalate an unresolved complaint to the HOD.
    Only use if prior resolution attempts with the teacher have failed.
    """
    from apps.agent.models import Complaint
    try:
        complaint = Complaint.objects.get(id=complaint_id)
    except Complaint.DoesNotExist:
        return {"error": f"Complaint #{complaint_id} not found."}

    complaint.status = "in_progress"
    complaint.save()

    try:
        requests.post(
            settings.N8N_WEBHOOK_ESCALATE,
            json={
                "complaint_id": complaint_id,
                "student_name": complaint.student.name,
                "roll_no": complaint.student.roll_no,
                "subject": complaint.subject,
                "description": complaint.description,
                "reason_for_escalation": reason,
                "hod_email": "hod.dsai@kfueit.edu.pk",
                "timestamp": str(complaint.created_at),
            },
            timeout=5,
        )
    except requests.RequestException:
        pass

    return {
        "success": True,
        "message": f"Complaint #{complaint_id} escalated to HOD. Audit trail recorded.",
    }


# ── Admissions / Policy Tool (Pinecone RAG) ───────────────────────────────────

@tool
def search_university_knowledge(
    query: str,
    roll_no: str = "",
    top_k: int = 5,
    include_public_fallback: bool = True,
) -> list[dict]:
    """
    Search KFUEIT knowledge base for policies, admissions, faculty, SFSC, fee structure, etc.
    Prefer the student's private namespace when roll_no is available.
    Fall back to the shared university namespace if enabled and needed.
    """
    if not settings.PINECONE_API_KEY or not settings.PINECONE_INDEX_NAME:
        return [{"text": "University knowledge base not configured (Pinecone index settings missing).", "source": "", "score": 0}]

    try:
        safe_top_k = max(1, min(int(top_k), 10))
        effective_roll_no = (roll_no or extract_roll_no_from_text(query)).strip()
        allow_public_fallback = (
            include_public_fallback and settings.PINECONE_ENABLE_PUBLIC_FALLBACK
        )

        if settings.PINECONE_REQUIRE_STUDENT_NAMESPACE_FOR_RAG and not effective_roll_no:
            return [{
                "text": "Student context is required before searching the knowledge base.",
                "source": "",
                "score": 0,
            }]

        namespaces = get_query_namespaces(
            roll_no=effective_roll_no,
            include_public_fallback=allow_public_fallback,
        )

        all_matches = []
        seen = set()
        for namespace in namespaces:
            results = search_text_records(
                namespace=namespace,
                query_text=query,
                top_k=safe_top_k,
                fields=[
                    settings.PINECONE_TEXT_FIELD,
                    "source_url",
                    "chunk_index",
                ],
            )

            namespace_matches = []
            for match in results.get("result", {}).get("hits", []):
                score = round(match.get("_score", 0), 3)
                if score <= 0:
                    continue
                fields = match.get("fields", {})
                item = {
                    "text": fields.get(settings.PINECONE_TEXT_FIELD, ""),
                    "source": fields.get("source_url", ""),
                    "score": score,
                    "namespace": namespace,
                }
                dedupe_key = (item["text"], item["source"], item["namespace"])
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                namespace_matches.append(item)
            if namespace_matches:
                all_matches.extend(namespace_matches)
                if namespace != namespaces[-1]:
                    break

        if not all_matches:
            if effective_roll_no and allow_public_fallback:
                return [{
                    "text": "No relevant information was found in the student's namespace or the public knowledge base.",
                    "source": "",
                    "score": 0,
                }]
            if effective_roll_no:
                return [{
                    "text": "No relevant information was found in the student's namespace.",
                    "source": "",
                    "score": 0,
                }]
            return [{"text": "No relevant information found in the knowledge base.", "source": "", "score": 0}]

        all_matches.sort(key=lambda item: item["score"], reverse=True)
        return all_matches[:safe_top_k]
    except Exception as e:
        return [{"text": f"Knowledge base search failed: {str(e)}", "source": "", "score": 0}]
