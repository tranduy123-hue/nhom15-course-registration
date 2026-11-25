import sqlite3
import pytest

from src.services.registration_service import RegistrationService
from src.services.schedule_tuition_service import (
    ScheduleTuitionService,
    StudentNotFoundForScheduleError,
)


@pytest.fixture
def db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    RegistrationService(conn)

    conn.execute(
        """
        INSERT INTO students (id, student_code, full_name, email, major, academic_year)
        VALUES (1, '25S1020102', 'Phan Thanh Thịnh', 'thinh@example.edu.vn', 'Sư phạm Tin học', 2025)
        """
    )
    conn.executemany(
        """
        INSERT INTO courses (id, course_code, course_name, credits, department)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (1, "TIN101", "Nhập môn Lập trình", 3, "CNTT"),
            (2, "TIN102", "Cấu trúc dữ liệu", 4, "CNTT"),
            (3, "MAT101", "Toán rời rạc", 2, "Toán - Tin"),
        ],
    )
    conn.executemany(
        """
        INSERT INTO class_sections (
            id, section_code, course_id, semester, max_capacity, enrolled_count,
            day_of_week, start_period, end_period, room, lecturer
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (10, "TIN101.01", 1, "2026-1", 40, 0, 2, 1, 3, "P.A101", "GV. Trần A"),
            (11, "TIN102.01", 2, "2026-1", 35, 0, 4, 4, 6, "P.B202", "GV. Lê B"),
            (12, "MAT101.01", 3, "2026-1", 50, 0, 2, 7, 8, "P.C303", "GV. Phạm C"),
            (13, "TIN101.02", 1, "2026-2", 40, 0, 3, 1, 3, "P.A102", "GV. Trần A"),
        ],
    )
    conn.commit()
    return conn


def test_personal_schedule_sorted_and_tuition_calculated(db_conn: sqlite3.Connection):
    reg = RegistrationService(db_conn)
    svc = ScheduleTuitionService(db_conn, tuition_per_credit=500_000)

    reg.register_course(student_id=1, section_id=12)  # MAT101: 2TC, Thứ 2 tiết 7-8
    reg.register_course(student_id=1, section_id=11)  # TIN102: 4TC, Thứ 4 tiết 4-6
    reg.register_course(student_id=1, section_id=10)  # TIN101: 3TC, Thứ 2 tiết 1-3
    reg.register_course(student_id=1, section_id=13)  # Kỳ 2026-2

    summary = svc.get_personal_schedule_and_tuition(student_id=1, semester="2026-1")
    assert summary.total_courses == 3
    assert summary.total_credits == 9
    assert summary.estimated_tuition == 4_500_000
    assert [item.course_code for item in summary.items] == ["TIN101", "MAT101", "TIN102"]
    assert summary.items[0].day_label == "Thứ 2"
    assert summary.items[0].tuition_amount == 1_500_000


def test_cancelled_enrollment_excluded_from_schedule_and_tuition(db_conn: sqlite3.Connection):
    reg = RegistrationService(db_conn)
    svc = ScheduleTuitionService(db_conn, tuition_per_credit=500_000)

    reg.register_course(student_id=1, section_id=10)  # 3TC
    reg.register_course(student_id=1, section_id=12)  # 2TC
    db_conn.execute(
        "UPDATE enrollments SET status = 'CANCELLED' WHERE student_id = 1 AND section_id = 10"
    )
    db_conn.commit()

    summary = svc.get_personal_schedule_and_tuition(student_id=1, semester="2026-1")
    assert summary.total_courses == 1
    assert summary.total_credits == 2
    assert summary.estimated_tuition == 1_000_000


def test_nonexistent_student_raises_error(db_conn: sqlite3.Connection):
    svc = ScheduleTuitionService(db_conn)
    with pytest.raises(StudentNotFoundForScheduleError):
        svc.get_personal_schedule_and_tuition(student_id=999)
