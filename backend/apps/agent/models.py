from django.db import models


class StudentProfile(models.Model):
    roll_no = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    program = models.CharField(max_length=100)
    section = models.CharField(max_length=20)
    cgpa = models.FloatField(default=0.0)
    credit_hours_req = models.IntegerField(default=132)
    credit_hours_done = models.IntegerField(default=0)
    degree_status = models.CharField(max_length=50, default="In Progress")
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.roll_no} - {self.name}"


class CourseEnrollment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="enrollments")
    course_code = models.CharField(max_length=20)
    course_name = models.CharField(max_length=100)
    credit_hours = models.IntegerField(default=3)
    section = models.CharField(max_length=20)
    semester = models.CharField(max_length=30, default="Spring 2026")

    def __str__(self):
        return f"{self.student.roll_no} - {self.course_code}"


class AttendanceRecord(models.Model):
    STATUS_CHOICES = [("P", "Present"), ("A", "Absent"), ("L", "Leave")]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="attendance_records")
    course_code = models.CharField(max_length=20)
    course_name = models.CharField(max_length=100)
    date_time = models.DateTimeField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)

    def __str__(self):
        return f"{self.student.roll_no} - {self.course_code} - {self.date_time.date()} - {self.status}"

    @property
    def attendance_summary(self):
        records = AttendanceRecord.objects.filter(
            student=self.student, course_code=self.course_code
        )
        total = records.count()
        present = records.filter(status="P").count()
        percent = round((present / total * 100), 1) if total > 0 else 0
        return {"present": present, "total": total, "percent": percent}


class TranscriptCourse(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="transcript")
    semester = models.CharField(max_length=30)
    course_code = models.CharField(max_length=20)
    course_name = models.CharField(max_length=100)
    grade = models.CharField(max_length=5)
    grade_point = models.FloatField()
    credit_hours = models.IntegerField()
    gpa_earned = models.FloatField()

    def __str__(self):
        return f"{self.student.roll_no} - {self.semester} - {self.course_code} - {self.grade}"


class SessionalMarks(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="sessional_marks")
    course_code = models.CharField(max_length=20)
    course_name = models.CharField(max_length=100)
    assignment_marks = models.FloatField(default=0)
    quiz_marks = models.FloatField(default=0)
    mid_marks = models.FloatField(default=0)
    total_obtained = models.FloatField(default=0)
    total_possible = models.FloatField(default=100)

    def __str__(self):
        return f"{self.student.roll_no} - {self.course_code} - {self.total_obtained}/{self.total_possible}"


class Complaint(models.Model):
    STATUS_CHOICES = [("open", "Open"), ("in_progress", "In Progress"), ("resolved", "Resolved")]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="complaints")
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.roll_no} - {self.subject} [{self.status}]"


class AgentLog(models.Model):
    roll_no = models.CharField(max_length=20)
    session_id = models.CharField(max_length=100)
    query = models.TextField()
    response = models.TextField()
    actor_used = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.roll_no} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
