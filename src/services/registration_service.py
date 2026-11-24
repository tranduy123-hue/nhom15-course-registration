"""
Atomic Course Registration Engine with Concurrency & Capacity Protection.
Task: DKMH-7 (US3)
Author: Trần Duy (tranduy123-hue)
"""
import sqlite3
from dataclasses import dataclass
from typing import Optional, Callable, Dict, Any


class RegistrationError(Exception):
    """Base exception for course registration failures."""
    pass


class CapacityExceededError(RegistrationError):
    """Raised when the class section has reached maximum capacity."""
    pass


class DuplicateCourseError(RegistrationError):
    """Raised when student tries to register more than one section of the same course in a semester."""
    pass


class SectionNotFoundError(RegistrationError):
    """Raised when the requested class section does not exist."""
    pass


class StudentNotFoundError(RegistrationError):
    """Raised when the student does not exist."""
    pass


class PrerequisiteNotMetError(RegistrationError):
    """Raised when student has not completed required prerequisites."""
    pass


class ScheduleConflictError(RegistrationError):
    """Raised when the section time conflicts with existing enrolled courses."""
    pass


@dataclass
class RegistrationResult:
    """Outcome payload of a course registration request."""
    success: bool
    enrollment_id: int
    student_id: int
    section_id: int
    course_name: str
    message: str


class RegistrationService:
    """
    Core transactional engine managing atomic class section enrollments.
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.init_schema()

    def init_schema(self) -> None:
        """Create necessary relational tables if not present."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_code TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE,
                major TEXT,
                academic_year INTEGER
            );

            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT UNIQUE NOT NULL,
                course_name TEXT NOT NULL,
                credits INTEGER NOT NULL CHECK(credits > 0),
                department TEXT
            );

            CREATE TABLE IF NOT EXISTS class_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_code TEXT UNIQUE NOT NULL,
                course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                semester TEXT NOT NULL,
                max_capacity INTEGER NOT NULL CHECK(max_capacity > 0),
                enrolled_count INTEGER NOT NULL DEFAULT 0 CHECK(enrolled_count >= 0),
                day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 2 AND 8),
                start_period INTEGER NOT NULL CHECK(start_period BETWEEN 1 AND 12),
                end_period INTEGER NOT NULL CHECK(end_period >= start_period),
                room TEXT,
                lecturer TEXT
            );

            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                section_id INTEGER NOT NULL REFERENCES class_sections(id) ON DELETE CASCADE,
                registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'ENROLLED' CHECK(status IN ('ENROLLED', 'CANCELLED')),
                UNIQUE(student_id, section_id)
            );
        """)
        self.conn.commit()

    def register_course(
        self,
        student_id: int,
        section_id: int,
        prerequisite_validator: Optional[Callable[[sqlite3.Connection, int, int], bool]] = None,
        conflict_detector: Optional[Callable[[sqlite3.Connection, int, Dict[str, Any]], bool]] = None
    ) -> RegistrationResult:
        """
        Execute an atomic enrollment transaction for a student into a class section.
        Protects against race conditions, capacity overflows, and duplicate course enrollments.
        """
        cursor = self.conn.cursor()

        try:
            # 1. Verify student existence
            cursor.execute("SELECT id, full_name FROM students WHERE id = ?", (student_id,))
            student_row = cursor.fetchone()
            if not student_row:
                raise StudentNotFoundError(f"Student ID {student_id} not found")

            # 2. Query target section with lock/atomicity in current transaction
            cursor.execute(
                """
                SELECT cs.id, cs.section_code, cs.course_id, c.course_name, cs.semester,
                       cs.max_capacity, cs.enrolled_count, cs.day_of_week, cs.start_period, cs.end_period
                FROM class_sections cs
                JOIN courses c ON cs.course_id = c.id
                WHERE cs.id = ?
                """,
                (section_id,)
            )
            section = cursor.fetchone()
            if not section:
                raise SectionNotFoundError(f"Class section ID {section_id} not found")

            (
                sec_id, sec_code, course_id, course_name, semester,
                max_capacity, enrolled_count, day_of_week, start_p, end_p
            ) = section

            # 3. Check section capacity
            if enrolled_count >= max_capacity:
                raise CapacityExceededError(
                    f"Class section '{sec_code}' is full (Capacity: {enrolled_count}/{max_capacity})"
                )

            # 4. Check duplicate course in the same semester
            cursor.execute(
                """
                SELECT cs.section_code
                FROM enrollments e
                JOIN class_sections cs ON e.section_id = cs.id
                WHERE e.student_id = ?
                  AND cs.course_id = ?
                  AND cs.semester = ?
                  AND e.status = 'ENROLLED'
                """,
                (student_id, course_id, semester)
            )
            existing_enrollment = cursor.fetchone()
            if existing_enrollment:
                raise DuplicateCourseError(
                    f"Student has already enrolled in another section ({existing_enrollment[0]}) of course '{course_name}'"
                )

            # 5. External validation hook: Prerequisites
            if prerequisite_validator:
                is_valid = prerequisite_validator(self.conn, student_id, course_id)
                if not is_valid:
                    raise PrerequisiteNotMetError(
                        f"Prerequisites not met for course '{course_name}'"
                    )

            # 6. External validation hook: Schedule conflicts
            if conflict_detector:
                section_info = {
                    "id": sec_id,
                    "day_of_week": day_of_week,
                    "start_period": start_p,
                    "end_period": end_p,
                    "semester": semester
                }
                has_conflict = conflict_detector(self.conn, student_id, section_info)
                if has_conflict:
                    raise ScheduleConflictError(
                        f"Schedule conflict detected for section '{sec_code}' (Day {day_of_week}, Periods {start_p}-{end_p})"
                    )

            # 7. Atomic capacity increment with guard condition
            cursor.execute(
                """
                UPDATE class_sections
                SET enrolled_count = enrolled_count + 1
                WHERE id = ? AND enrolled_count < max_capacity
                """,
                (section_id,)
            )
            if cursor.rowcount != 1:
                raise CapacityExceededError(
                    f"Class section '{sec_code}' was filled concurrently by another student"
                )

            # 8. Record active enrollment
            cursor.execute(
                """
                INSERT INTO enrollments (student_id, section_id, status)
                VALUES (?, ?, 'ENROLLED')
                ON CONFLICT(student_id, section_id) DO UPDATE SET
                    status = 'ENROLLED',
                    registered_at = CURRENT_TIMESTAMP
                """,
                (student_id, section_id)
            )
            enrollment_id = cursor.lastrowid
            self.conn.commit()

            return RegistrationResult(
                success=True,
                enrollment_id=enrollment_id,
                student_id=student_id,
                section_id=section_id,
                course_name=course_name,
                message=f"Successfully registered section '{sec_code}' for course '{course_name}'"
            )

        except Exception:
            self.conn.rollback()
            raise
