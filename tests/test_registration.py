"""
Unit Tests for Atomic Course Registration Engine.
Task: DKMH-7 (US3)
Author: Trần Duy (tranduy123-hue)
"""
import sqlite3
import pytest
from src.services.registration_service import (
    RegistrationService,
    CapacityExceededError,
    DuplicateCourseError,
    SectionNotFoundError,
    StudentNotFoundError,
    PrerequisiteNotMetError,
    ScheduleConflictError
)


@pytest.fixture
def reg_env():
    """Initializes in-memory database with standard courses, sections, and students."""
    conn = sqlite3.connect(":memory:")
    service = RegistrationService(conn)
    cursor = conn.cursor()

    # Seed student
    cursor.execute("""
        INSERT INTO students (id, student_code, full_name, email, major, academic_year)
        VALUES (1, '20T1020001', 'Trần Duy', 'duy@example.com', 'CNTT', 2026)
    """)

    # Seed courses
    cursor.execute("""
        INSERT INTO courses (id, course_code, course_name, credits, department)
        VALUES
            (10, 'CS101', 'Nhập môn Lập trình', 3, 'Khoa CNTT'),
            (20, 'CS102', 'Kỹ thuật Lập trình', 3, 'Khoa CNTT'),
            (30, 'MATH101', 'Giải tích 1', 4, 'Khoa Toán')
    """)

    # Seed sections
    # Section 101: Available (Capacity 2, Enrolled 0)
    cursor.execute("""
        INSERT INTO class_sections (id, section_code, course_id, semester, max_capacity, enrolled_count, day_of_week, start_period, end_period, room, lecturer)
        VALUES (101, 'CS101.01', 10, '2026_HK1', 2, 0, 2, 1, 3, 'A101', 'Thầy Long Tran')
    """)

    # Section 102: Same course CS101, different section (Capacity 2, Enrolled 0)
    cursor.execute("""
        INSERT INTO class_sections (id, section_code, course_id, semester, max_capacity, enrolled_count, day_of_week, start_period, end_period, room, lecturer)
        VALUES (102, 'CS101.02', 10, '2026_HK1', 2, 0, 4, 4, 6, 'A102', 'Cô Mai')
    """)

    # Section 201: Full section (Capacity 1, Enrolled 1)
    cursor.execute("""
        INSERT INTO class_sections (id, section_code, course_id, semester, max_capacity, enrolled_count, day_of_week, start_period, end_period, room, lecturer)
        VALUES (201, 'CS102.01', 20, '2026_HK1', 1, 1, 3, 1, 3, 'B201', 'Thầy Hưng')
    """)

    conn.commit()
    yield service, conn
    conn.close()


class TestRegistrationSuccess:
    def test_successful_enrollment_increments_enrolled_count(self, reg_env):
        service, conn = reg_env
        result = service.register_course(student_id=1, section_id=101)

        assert result.success is True
        assert result.course_name == "Nhập môn Lập trình"
        assert result.section_id == 101

        # Verify enrolled_count increased to 1
        cursor = conn.cursor()
        cursor.execute("SELECT enrolled_count FROM class_sections WHERE id = 101")
        assert cursor.fetchone()[0] == 1

        # Verify enrollment record exists
        cursor.execute(
            "SELECT status FROM enrollments WHERE student_id = 1 AND section_id = 101"
        )
        assert cursor.fetchone()[0] == "ENROLLED"


class TestRegistrationCapacityProtection:
    def test_registration_fails_when_section_is_full(self, reg_env):
        service, conn = reg_env
        with pytest.raises(CapacityExceededError, match="is full"):
            service.register_course(student_id=1, section_id=201)

        # Enrolled count remains 1
        cursor = conn.cursor()
        cursor.execute("SELECT enrolled_count FROM class_sections WHERE id = 201")
        assert cursor.fetchone()[0] == 1


class TestRegistrationDuplicateCourseProtection:
    def test_registration_fails_for_duplicate_course_in_same_semester(self, reg_env):
        service, conn = reg_env
        # Register section 101 (CS101)
        service.register_course(student_id=1, section_id=101)

        # Attempt to register section 102 (CS101)
        with pytest.raises(DuplicateCourseError, match="already enrolled in another section"):
            service.register_course(student_id=1, section_id=102)


class TestRegistrationValidationHooks:
    def test_registration_fails_when_prerequisite_not_met(self, reg_env):
        service, conn = reg_env

        def mock_prereq_fail(db_conn, student_id, course_id):
            return False

        with pytest.raises(PrerequisiteNotMetError, match="Prerequisites not met"):
            service.register_course(
                student_id=1,
                section_id=101,
                prerequisite_validator=mock_prereq_fail
            )

    def test_registration_fails_when_schedule_conflicts(self, reg_env):
        service, conn = reg_env

        def mock_conflict_detector(db_conn, student_id, section_info):
            return True

        with pytest.raises(ScheduleConflictError, match="Schedule conflict detected"):
            service.register_course(
                student_id=1,
                section_id=101,
                conflict_detector=mock_conflict_detector
            )


class TestRegistrationNonexistentEntities:
    def test_invalid_student_id_raises_error(self, reg_env):
        service, conn = reg_env
        with pytest.raises(StudentNotFoundError):
            service.register_course(student_id=999, section_id=101)

    def test_invalid_section_id_raises_error(self, reg_env):
        service, conn = reg_env
        with pytest.raises(SectionNotFoundError):
            service.register_course(student_id=1, section_id=9999)
