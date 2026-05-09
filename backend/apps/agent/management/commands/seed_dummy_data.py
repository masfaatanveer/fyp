import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.agent.models import (
    StudentProfile, CourseEnrollment, AttendanceRecord,
    TranscriptCourse, SessionalMarks, Complaint
)


CURRENT_SEMESTER = "Spring 2026"

CURRENT_COURSES = [
    {"code": "COSC-4150", "name": "Routing & Switching", "credit_hours": 2},
    {"code": "COSC-4130", "name": "Reinforcement Learning", "credit_hours": 3},
    {"code": "MSCI-3111", "name": "Entrepreneurship", "credit_hours": 3},
    {"code": "COSC-4302", "name": "FYP-II", "credit_hours": 3},
]

STUDENTS = [
    {
        "roll_no": "COSC221103029",
        "name": "Masfa Tanveer",
        "program": "BS Artificial Intelligence",
        "section": "BS-AINT-8A",
        "cgpa": 3.15,
        "credit_hours_req": 132,
        "credit_hours_done": 121,
        "phone": "+92-300-0000029",
        "email": "masfa@student.kfueit.edu.pk",
    },
    {
        "roll_no": "COSC221103026",
        "name": "Areeba Zameer",
        "program": "BS Artificial Intelligence",
        "section": "BS-AINT-8A",
        "cgpa": 3.42,
        "credit_hours_req": 132,
        "credit_hours_done": 121,
        "phone": "+92-300-0000026",
        "email": "areeba@student.kfueit.edu.pk",
    },
    {
        "roll_no": "COSC221103031",
        "name": "Hamza Khalid",
        "program": "BS Artificial Intelligence",
        "section": "BS-AINT-8A",
        "cgpa": 2.87,
        "credit_hours_req": 132,
        "credit_hours_done": 121,
        "phone": "+92-300-0000031",
        "email": "hamza.khalid@student.kfueit.edu.pk",
    },
    {
        "roll_no": "COSC221103045",
        "name": "Sana Akram",
        "program": "BS Artificial Intelligence",
        "section": "BS-AINT-8A",
        "cgpa": 3.61,
        "credit_hours_req": 132,
        "credit_hours_done": 121,
        "phone": "+92-300-0000045",
        "email": "sana.akram@student.kfueit.edu.pk",
    },
    {
        "roll_no": "COSC221103052",
        "name": "Bilal Raza",
        "program": "BS Artificial Intelligence",
        "section": "BS-AINT-8A",
        "cgpa": 2.95,
        "credit_hours_req": 132,
        "credit_hours_done": 121,
        "phone": "+92-300-0000052",
        "email": "bilal.raza@student.kfueit.edu.pk",
    },
    {
        "roll_no": "COSC221103038",
        "name": "Nida Farooq",
        "program": "BS Artificial Intelligence",
        "section": "BS-AINT-8A",
        "cgpa": 3.28,
        "credit_hours_req": 132,
        "credit_hours_done": 121,
        "phone": "+92-300-0000038",
        "email": "nida.farooq@student.kfueit.edu.pk",
    },
]

# Masfa's real transcript data
MASFA_TRANSCRIPT = [
    # Fall 2022 (Semester 1)
    {"semester": "Fall 2022", "course_code": "COSC-1101", "course_name": "Introduction to Computing", "grade": "A", "grade_point": 4.0, "credit_hours": 3, "gpa_earned": 12.0},
    {"semester": "Fall 2022", "course_code": "MATH-1101", "course_name": "Calculus & Analytical Geometry", "grade": "B+", "grade_point": 3.5, "credit_hours": 3, "gpa_earned": 10.5},
    {"semester": "Fall 2022", "course_code": "PHYS-1101", "course_name": "Applied Physics", "grade": "B", "grade_point": 3.0, "credit_hours": 3, "gpa_earned": 9.0},
    {"semester": "Fall 2022", "course_code": "ENGL-1101", "course_name": "Functional English", "grade": "A-", "grade_point": 3.7, "credit_hours": 3, "gpa_earned": 11.1},
    {"semester": "Fall 2022", "course_code": "ISLA-1101", "course_name": "Islamic Studies", "grade": "A", "grade_point": 4.0, "credit_hours": 2, "gpa_earned": 8.0},
    {"semester": "Fall 2022", "course_code": "COSC-1102", "course_name": "Programming Fundamentals", "grade": "A", "grade_point": 4.0, "credit_hours": 3, "gpa_earned": 12.0},
    {"semester": "Fall 2022", "course_code": "MATH-1102", "course_name": "Discrete Mathematics", "grade": "C+", "grade_point": 2.5, "credit_hours": 3, "gpa_earned": 7.5},
    {"semester": "Fall 2022", "course_code": "COSC-1103", "course_name": "Digital Logic Design", "grade": "B+", "grade_point": 3.5, "credit_hours": 3, "gpa_earned": 10.5},
    # Spring 2023 (Semester 2)
    {"semester": "Spring 2023", "course_code": "COSC-2101", "course_name": "Object Oriented Programming", "grade": "A-", "grade_point": 3.7, "credit_hours": 3, "gpa_earned": 11.1},
    {"semester": "Spring 2023", "course_code": "COSC-2102", "course_name": "Data Structures & Algorithms", "grade": "B+", "grade_point": 3.5, "credit_hours": 3, "gpa_earned": 10.5},
    {"semester": "Spring 2023", "course_code": "MATH-2101", "course_name": "Linear Algebra", "grade": "A", "grade_point": 4.0, "credit_hours": 3, "gpa_earned": 12.0},
    {"semester": "Spring 2023", "course_code": "COSC-2103", "course_name": "Computer Organization & Architecture", "grade": "B", "grade_point": 3.0, "credit_hours": 3, "gpa_earned": 9.0},
    {"semester": "Spring 2023", "course_code": "ENGL-2101", "course_name": "Technical Report Writing", "grade": "A", "grade_point": 4.0, "credit_hours": 2, "gpa_earned": 8.0},
    {"semester": "Spring 2023", "course_code": "MATH-2102", "course_name": "Probability & Statistics", "grade": "B+", "grade_point": 3.5, "credit_hours": 3, "gpa_earned": 10.5},
    {"semester": "Spring 2023", "course_code": "COSC-2104", "course_name": "Database Systems", "grade": "A-", "grade_point": 3.7, "credit_hours": 3, "gpa_earned": 11.1},
    # Fall 2023 (Semester 3)
    {"semester": "Fall 2023", "course_code": "COSC-3101", "course_name": "Operating Systems", "grade": "B+", "grade_point": 3.5, "credit_hours": 3, "gpa_earned": 10.5},
    {"semester": "Fall 2023", "course_code": "COSC-3102", "course_name": "Artificial Intelligence", "grade": "A", "grade_point": 4.0, "credit_hours": 3, "gpa_earned": 12.0},
    {"semester": "Fall 2023", "course_code": "COSC-3103", "course_name": "Computer Networks", "grade": "C+", "grade_point": 2.5, "credit_hours": 3, "gpa_earned": 7.5},
    {"semester": "Fall 2023", "course_code": "COSC-3104", "course_name": "Software Engineering", "grade": "D", "grade_point": 1.0, "credit_hours": 3, "gpa_earned": 3.0},
    # Spring 2024 (Semester 4)
    {"semester": "Spring 2024", "course_code": "COSC-3201", "course_name": "Machine Learning", "grade": "A-", "grade_point": 3.7, "credit_hours": 3, "gpa_earned": 11.1},
    {"semester": "Spring 2024", "course_code": "COSC-3202", "course_name": "Deep Learning", "grade": "B+", "grade_point": 3.5, "credit_hours": 3, "gpa_earned": 10.5},
    {"semester": "Spring 2024", "course_code": "COSC-3203", "course_name": "Natural Language Processing", "grade": "B+", "grade_point": 3.5, "credit_hours": 3, "gpa_earned": 10.5},
    {"semester": "Spring 2024", "course_code": "COSC-3204", "course_name": "Computer Vision", "grade": "A", "grade_point": 4.0, "credit_hours": 3, "gpa_earned": 12.0},
    {"semester": "Spring 2024", "course_code": "MSCI-3101", "course_name": "Engineering Management", "grade": "B", "grade_point": 3.0, "credit_hours": 2, "gpa_earned": 6.0},
    # Fall 2024 (Semester 5)
    {"semester": "Fall 2024", "course_code": "COSC-4101", "course_name": "Cloud Computing", "grade": "A-", "grade_point": 3.7, "credit_hours": 3, "gpa_earned": 11.1},
    {"semester": "Fall 2024", "course_code": "COSC-4102", "course_name": "Cybersecurity", "grade": "B", "grade_point": 3.0, "credit_hours": 3, "gpa_earned": 9.0},
    {"semester": "Fall 2024", "course_code": "COSC-4103", "course_name": "Data Mining", "grade": "A", "grade_point": 4.0, "credit_hours": 3, "gpa_earned": 12.0},
    {"semester": "Fall 2024", "course_code": "COSC-4104", "course_name": "Big Data Analytics", "grade": "B+", "grade_point": 3.5, "credit_hours": 3, "gpa_earned": 10.5},
    # Spring 2025 (Semester 6)
    {"semester": "Spring 2025", "course_code": "COSC-4201", "course_name": "Generative AI", "grade": "A", "grade_point": 4.0, "credit_hours": 3, "gpa_earned": 12.0},
    {"semester": "Spring 2025", "course_code": "COSC-4202", "course_name": "MLOps", "grade": "B+", "grade_point": 3.5, "credit_hours": 3, "gpa_earned": 10.5},
    {"semester": "Spring 2025", "course_code": "COSC-4203", "course_name": "Distributed Systems", "grade": "B", "grade_point": 3.0, "credit_hours": 3, "gpa_earned": 9.0},
    {"semester": "Spring 2025", "course_code": "COSC-4301", "course_name": "FYP-I", "grade": "A-", "grade_point": 3.7, "credit_hours": 3, "gpa_earned": 11.1},
]


def random_date_in_range(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)


class Command(BaseCommand):
    help = "Seed dummy student data with Masfa's real academic records"

    def handle(self, *args, **options):
        self.stdout.write("Clearing old data...")
        StudentProfile.objects.all().delete()

        self.stdout.write("Seeding students...")
        for s_data in STUDENTS:
            student = StudentProfile.objects.create(**s_data)
            self.seed_enrollments(student)
            self.seed_attendance(student)
            self.seed_transcript(student)
            self.seed_sessional_marks(student)
            self.stdout.write(f"  Seeded: {student.roll_no} - {student.name}")

        self.stdout.write(self.style.SUCCESS(f"Done! Seeded {len(STUDENTS)} students."))

    def seed_enrollments(self, student):
        for course in CURRENT_COURSES:
            CourseEnrollment.objects.create(
                student=student,
                course_code=course["code"],
                course_name=course["name"],
                credit_hours=course["credit_hours"],
                section=student.section,
                semester=CURRENT_SEMESTER,
            )

    def seed_attendance(self, student):
        # Generate 12 class records per course, mostly present
        base_date = datetime(2026, 1, 13, tzinfo=timezone.get_current_timezone())
        for course in CURRENT_COURSES:
            for i in range(12):
                class_date = base_date + timedelta(weeks=i)
                # ~83% attendance (10/12 present on average)
                if i < 10:
                    status = "P"
                elif i == 10:
                    status = "A" if random.random() < 0.5 else "P"
                else:
                    status = "A"
                AttendanceRecord.objects.create(
                    student=student,
                    course_code=course["code"],
                    course_name=course["name"],
                    date_time=class_date,
                    status=status,
                )

    def seed_transcript(self, student):
        if student.roll_no == "COSC221103029":
            # Masfa's real transcript
            for tc in MASFA_TRANSCRIPT:
                TranscriptCourse.objects.create(student=student, **tc)
        else:
            # Generate plausible transcript for classmates
            for tc in MASFA_TRANSCRIPT:
                gp_variation = random.choice([-0.3, 0.0, 0.3, 0.7])
                new_gp = max(1.0, min(4.0, round(tc["grade_point"] + gp_variation, 1)))
                grade_map = {4.0: "A", 3.7: "A-", 3.5: "B+", 3.0: "B", 2.5: "C+", 2.0: "C", 1.0: "D"}
                new_grade = grade_map.get(new_gp, tc["grade"])
                TranscriptCourse.objects.create(
                    student=student,
                    semester=tc["semester"],
                    course_code=tc["course_code"],
                    course_name=tc["course_name"],
                    grade=new_grade,
                    grade_point=new_gp,
                    credit_hours=tc["credit_hours"],
                    gpa_earned=round(new_gp * tc["credit_hours"], 1),
                )

    def seed_sessional_marks(self, student):
        for course in CURRENT_COURSES:
            assignment = round(random.uniform(12, 18), 1)
            quiz = round(random.uniform(10, 17), 1)
            mid = round(random.uniform(20, 32), 1)
            total = assignment + quiz + mid
            SessionalMarks.objects.create(
                student=student,
                course_code=course["code"],
                course_name=course["name"],
                assignment_marks=assignment,
                quiz_marks=quiz,
                mid_marks=mid,
                total_obtained=round(total, 1),
                total_possible=70,
            )
