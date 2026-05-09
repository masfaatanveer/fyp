import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

from .services.supervisor import run_agent


def _validate_roll_no(roll_no: str):
    """
    Best-effort validation for demo mode.
    In production LMS mode, identity should come from authenticated LMS context.
    """
    if not roll_no:
        return False, JsonResponse({"error": "roll_no is required."}, status=400)

    from django.conf import settings

    if settings.USE_DUMMY_DATA:
        from .models import StudentProfile

        if not StudentProfile.objects.filter(roll_no=roll_no).exists():
            return False, JsonResponse(
                {"error": f"Student with roll number {roll_no} was not found."},
                status=404,
            )

    return True, None


@csrf_exempt
@require_POST
def agent_query(request):
    """
    POST /api/agent/query/
    Body: { "query": "...", "roll_no": "COSC221103029", "session_id": "optional-uuid" }
    Returns: { "response": "..." }
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    query = body.get("query", "").strip()
    roll_no = body.get("roll_no", "").strip()
    session_id = body.get("session_id") or str(uuid.uuid4())

    if not query:
        return JsonResponse({"error": "Query is required."}, status=400)
    is_valid_roll, error_response = _validate_roll_no(roll_no)
    if not is_valid_roll:
        return error_response

    thread_id = f"student_{roll_no}_{session_id}"

    response_text = run_agent(query=query, roll_no=roll_no, thread_id=thread_id)

    return JsonResponse({"response": response_text, "session_id": session_id})


@csrf_exempt
@require_POST
def vapi_webhook(request):
    """
    POST /api/agent/vapi/
    Vapi calls this endpoint when a voice message is transcribed.
    Body: { "message": { "type": "transcript", "transcript": "..." }, ... }
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    msg = body.get("message", {})
    msg_type = msg.get("type")

    if msg_type == "transcript" and msg.get("transcriptType") == "final":
        transcript = msg.get("transcript", "")
        call_id = body.get("call", {}).get("id", str(uuid.uuid4()))

        # Extract roll_no from Vapi call metadata if passed during call start
        roll_no = body.get("call", {}).get("metadata", {}).get("roll_no", "UNKNOWN")
        is_valid_roll, error_response = _validate_roll_no(roll_no)
        if not is_valid_roll:
            return error_response

        response_text = run_agent(query=transcript, roll_no=roll_no, thread_id=f"vapi_{call_id}")

        return JsonResponse({"response": response_text})

    return JsonResponse({"status": "ignored"})


def student_lookup(request, roll_no):
    """
    GET /api/agent/student/<roll_no>/
    Returns basic student info for identity verification before chat starts.
    """
    from .models import StudentProfile
    try:
        student = StudentProfile.objects.get(roll_no=roll_no.strip().upper())
        return JsonResponse({
            "roll_no": student.roll_no,
            "name": student.name,
            "program": student.program,
            "section": student.section,
        })
    except StudentProfile.DoesNotExist:
        return JsonResponse({"error": "Student not found."}, status=404)


def admin_logs(request):
    """
    GET /api/agent/admin/logs/?roll_no=COSC221103029&limit=50
    Returns recent agent conversation logs.
    """
    from .models import AgentLog
    roll_no = request.GET.get("roll_no")
    limit = int(request.GET.get("limit", 50))

    qs = AgentLog.objects.order_by("-created_at")
    if roll_no:
        qs = qs.filter(roll_no=roll_no)
    qs = qs[:limit]

    logs = [
        {
            "id": log.id,
            "roll_no": log.roll_no,
            "session_id": log.session_id,
            "query": log.query,
            "response": log.response,
            "actor_used": log.actor_used,
            "created_at": log.created_at.isoformat(),
        }
        for log in qs
    ]
    return JsonResponse({"logs": logs, "count": len(logs)})
