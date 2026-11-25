"""
Course Cancellation / Withdrawal Service.
Task: DKMH-9 (US5)
"""
import sqlite3
from dataclasses import dataclass
from typing import Any, Callable, Optional


class CancellationError(Exception):
    """Base exception for course cancellation / withdrawal failures."""


class StudentNotFoundForCancelError(CancellationError):
    """Raised when the student does not exist."""


class SectionNotFoundForCancelError(CancellationError):
    """Raised when the class section does not exist."""


class EnrollmentNotFoundError(CancellationError):
    """Raised when no active enrollment exists for the student in the section."""


class CancellationDeadlineError(CancellationError):
    """Raised when cancellation is attempted outside the allowed period."""


@dataclass
class CancellationResult:
    """Outcome payload of a course cancellation / withdrawal request."""
    success: bool
    enrollment_id: int
    student_id: int
    section_id: int
    course_code: str
    course_name: str
    section_code: str
    semester: str
    status: str
    enrolled_count: int
    message: str


def _resolve_conn(db: Any) -> tuple[sqlite3.Connection, bool]:
    if hasattr(db, "get_connection"):
        conn = db.get_connection()
        conn.row_factory = sqlite3.Row
        return conn, True
    db.row_factory = sqlite3.Row
    return db, False


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cursor = conn.execute(f"PRAGMA table_info({table});")
    return any(row[1] == column for row in cursor.fetchall())


class EnrollmentCancellationService:
    """Service handling student withdrawal / cancellation from registered class sections."""

    ACTIVE_STATUSES = ("ENROLLED", "REGISTERED")

    def __init__(self, db: Any) -> None:
        self.db = db

    def cancel_enrollment(
        self,
        student_id: int,
        section_id: int,
        deadline_validator: Optional[Callable[[sqlite3.Connection, int, int, str], bool]] = None,
    ) -> CancellationResult:
        """
        Cancel an active enrollment for a student in a class section and decrement
        enrolled_count atomically.
        """
        conn, should_close = _resolve_conn(self.db)
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()

            # 1. Verify student exists
            student_row = cursor.execute(
                "SELECT id, full_name FROM students WHERE id = ?",
                (student_id,),
            ).fetchone()
            if not student_row:
                raise StudentNotFoundForCancelError(f"Student ID {student_id} not found")

            # 2. Verify section and course exist
            section_row = cursor.execute(
                """
                SELECT cs.id, cs.section_code, cs.semester, cs.enrolled_count,
                       c.course_code, c.course_name
                FROM class_sections cs
                JOIN courses c ON cs.course_id = c.id
                WHERE cs.id = ?
                """,
                (section_id,),
            ).fetchone()
            if not section_row:
                raise SectionNotFoundForCancelError(f"Class section ID {section_id} not found")

            semester = section_row["semester"]

            # 3. Optional deadline / policy check hook
            if deadline_validator is not None:
                allowed = deadline_validator(conn, student_id, section_id, semester)
                if not allowed:
                    raise CancellationDeadlineError(
                        f"Cancellation period closed for section '{section_row['section_code']}' in semester '{semester}'"
                    )

            # 4. Find active enrollment
            placeholders = ",".join("?" for _ in self.ACTIVE_STATUSES)
            enrollment_row = cursor.execute(
                f"""
                SELECT id, status
                FROM enrollments
                WHERE student_id = ?
                  AND section_id = ?
                  AND UPPER(status) IN ({placeholders})
                """,
                (student_id, section_id, *self.ACTIVE_STATUSES),
            ).fetchone()

            if not enrollment_row:
                raise EnrollmentNotFoundError(
                    f"No active enrollment found for student {student_id} in section {section_id}"
                )

            enrollment_id = int(enrollment_row["id"])

            # 5. Mark enrollment CANCELLED
            if _has_column(conn, "enrollments", "cancelled_at"):
                cursor.execute(
                    """
                    UPDATE enrollments
                    SET status = 'CANCELLED', cancelled_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (enrollment_id,),
                )
            else:
                cursor.execute(
                    """
                    UPDATE enrollments
                    SET status = 'CANCELLED'
                    WHERE id = ?
                    """,
                    (enrollment_id,),
                )

            # 6. Atomically decrement enrolled_count (never below 0)
            cursor.execute(
                """
                UPDATE class_sections
                SET enrolled_count = CASE
                    WHEN enrolled_count > 0 THEN enrolled_count - 1
                    ELSE 0
                END
                WHERE id = ?
                """,
                (section_id,),
            )

            updated_section = cursor.execute(
                "SELECT enrolled_count FROM class_sections WHERE id = ?",
                (section_id,),
            ).fetchone()
            new_enrolled_count = int(updated_section["enrolled_count"]) if updated_section else 0

            conn.commit()

            return CancellationResult(
                success=True,
                enrollment_id=enrollment_id,
                student_id=student_id,
                section_id=section_id,
                course_code=section_row["course_code"],
                course_name=section_row["course_name"],
                section_code=section_row["section_code"],
                semester=semester,
                status="CANCELLED",
                enrolled_count=new_enrolled_count,
                message=(
                    f"Cancelled enrollment for '{section_row['course_code']} - {section_row['course_name']}' "
                    f"(Section {section_row['section_code']})"
                ),
            )
        except Exception:
            conn.rollback()
            raise
        finally:
            if should_close:
                conn.close()
