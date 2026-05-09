from django.contrib import admin

from .models import (
    AgentLog,
    AttendanceRecord,
    Complaint,
    CourseEnrollment,
    SessionalMarks,
    StudentProfile,
    TranscriptCourse,
)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "roll_no",
        "name",
        "program",
        "section",
        "cgpa",
        "credit_hours_done",
        "degree_status",
    )
    search_fields = ("roll_no", "name", "email", "program", "section")
    list_filter = ("program", "section", "degree_status")
    ordering = ("roll_no",)


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course_code",
        "course_name",
        "credit_hours",
        "section",
        "semester",
    )
    search_fields = (
        "student__roll_no",
        "student__name",
        "course_code",
        "course_name",
        "semester",
    )
    list_filter = ("semester", "section", "credit_hours")
    ordering = ("student__roll_no", "course_code")


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course_code",
        "course_name",
        "date_time",
        "status",
    )
    search_fields = (
        "student__roll_no",
        "student__name",
        "course_code",
        "course_name",
    )
    list_filter = ("status", "course_code", "date_time")
    ordering = ("-date_time",)


@admin.register(TranscriptCourse)
class TranscriptCourseAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "semester",
        "course_code",
        "course_name",
        "grade",
        "grade_point",
        "credit_hours",
    )
    search_fields = (
        "student__roll_no",
        "student__name",
        "semester",
        "course_code",
        "course_name",
        "grade",
    )
    list_filter = ("semester", "grade", "credit_hours")
    ordering = ("student__roll_no", "semester", "course_code")


@admin.register(SessionalMarks)
class SessionalMarksAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course_code",
        "course_name",
        "assignment_marks",
        "quiz_marks",
        "mid_marks",
        "total_obtained",
        "total_possible",
    )
    search_fields = (
        "student__roll_no",
        "student__name",
        "course_code",
        "course_name",
    )
    list_filter = ("course_code",)
    ordering = ("student__roll_no", "course_code")


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "subject",
        "status",
        "created_at",
        "resolved_at",
    )
    search_fields = (
        "student__roll_no",
        "student__name",
        "subject",
        "description",
    )
    list_filter = ("status", "created_at", "resolved_at")
    ordering = ("-created_at",)


@admin.register(AgentLog)
class AgentLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "roll_no",
        "session_id",
        "actor_used",
        "created_at",
    )
    search_fields = (
        "roll_no",
        "session_id",
        "query",
        "response",
        "actor_used",
    )
    list_filter = ("actor_used", "created_at")
    ordering = ("-created_at",)
