import sqlite3
import pytest

from src.services.enrollment_service import (
    CancellationDeadlineError,
    EnrollmentCancellationService,
    EnrollmentNotFoundError,
    SectionNotFoundForCancelError,
    StudentNotFoundForCancelError,
)
from src.services.registration_service import RegistrationService


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
    conn.execute(
        """
        INSERT INTO courses (id, course_code, course_name, credits, department)
        VALUES (1, 'TIN101', 'Nhập môn Lập trình', 3, 'CNTT')
        """
    )
    conn.execute(
        """
        INSERT INTO class_sections (
            id, section_code, course_id, semester, max_capacity, enrolled_count,
            day_of_week, start_period, end_period, room, lecturer
        )
        VALUES (10, 'TIN101.01', 1, '2026-1', 40, 0, 2, 1, 3, 'P.A101', 'GV. Trần A')
        """
    )
    conn.commit()
    return conn


def test_cancel_enrollment_decrements_capacity_and_updates_status(db_conn: sqlite3.Connection):
    reg = RegistrationService(db_conn)
    cancel = EnrollmentCancellationService(db_conn)

    reg.register_course(student_id=1, section_id=10)
    assert db_conn.execute("SELECT enrolled_count FROM class_sections WHERE id = 10").fetchone()[0] == 1

    result = cancel.cancel_enrollment(student_id=1, section_id=10)
    assert result.success is True
    assert result.status == "CANCELLED"
    assert result.enrolled_count == 0
    assert result.course_code == "TIN101"

    status = db_conn.execute(
        "SELECT status FROM enrollments WHERE student_id = 1 AND section_id = 10"
    ).fetchone()[0]
    assert status == "CANCELLED"


def test_cancel_nonexistent_enrollment_raises_error(db_conn: sqlite3.Connection):
    cancel = EnrollmentCancellationService(db_conn)
    with pytest.raises(EnrollmentNotFoundError):
        cancel.cancel_enrollment(student_id=1, section_id=10)


def test_cancel_invalid_student_or_section_raises_error(db_conn: sqlite3.Connection):
    cancel = EnrollmentCancellationService(db_conn)
    with pytest.raises(StudentNotFoundForCancelError):
        cancel.cancel_enrollment(student_id=999, section_id=10)

    with pytest.raises(SectionNotFoundForCancelError):
        cancel.cancel_enrollment(student_id=1, section_id=999)


def test_cancel_blocked_by_deadline_hook(db_conn: sqlite3.Connection):
    reg = RegistrationService(db_conn)
    cancel = EnrollmentCancellationService(db_conn)
    reg.register_course(student_id=1, section_id=10)

    with pytest.raises(CancellationDeadlineError):
        cancel.cancel_enrollment(
            student_id=1,
            section_id=10,
            deadline_validator=lambda _conn, _sid, _sec, _sem: False,
        )

    assert db_conn.execute("SELECT enrolled_count FROM class_sections WHERE id = 10").fetchone()[0] == 1
