"""
Personal Timetable View and Estimated Tuition Calculation Service.
Task: DKMH-10 (US6)
"""
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


DEFAULT_TUITION_PER_CREDIT = 500_000  # VNĐ / tín chỉ (mặc định tạm tính)

DAY_NAMES: Dict[int, str] = {
    2: "Thứ 2",
    3: "Thứ 3",
    4: "Thứ 4",
    5: "Thứ 5",
    6: "Thứ 6",
    7: "Thứ 7",
    8: "Chủ nhật",
}


class ScheduleTuitionError(Exception):
    """Base exception for schedule and tuition queries."""


class StudentNotFoundForScheduleError(ScheduleTuitionError):
    """Raised when querying timetable/tuition for a non-existent student."""


@dataclass
class TimetableItem:
    enrollment_id: int
    section_id: int
    section_code: str
    course_id: int
    course_code: str
    course_name: str
    credits: int
    semester: str
    day_of_week: int
    day_label: str
    start_period: int
    end_period: int
    room: str
    lecturer: str
    tuition_amount: int


@dataclass
class PersonalScheduleTuitionSummary:
    student_id: int
    semester: Optional[str]
    tuition_per_credit: int
    total_courses: int
    total_credits: int
    estimated_tuition: int
    items: List[TimetableItem] = field(default_factory=list)


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


class ScheduleTuitionService:
    """Service providing personal student timetable and provisional tuition calculation."""

    ACTIVE_STATUSES = ("ENROLLED", "REGISTERED")

    def __init__(self, db: Any, tuition_per_credit: int = DEFAULT_TUITION_PER_CREDIT) -> None:
        if tuition_per_credit < 0:
            raise ValueError("Tuition per credit cannot be negative")
        self.db = db
        self.tuition_per_credit = tuition_per_credit

    def get_personal_schedule_and_tuition(
        self,
        student_id: int,
        semester: Optional[str] = None,
        tuition_per_credit: Optional[int] = None,
    ) -> PersonalScheduleTuitionSummary:
        """
        Retrieve active enrolled sections sorted by day and period, and calculate
        estimated tuition based on enrolled credits.
        """
        rate = self.tuition_per_credit if tuition_per_credit is None else tuition_per_credit
        if rate < 0:
            raise ValueError("Tuition per credit cannot be negative")

        conn, should_close = _resolve_conn(self.db)
        try:
            cursor = conn.cursor()

            student_row = cursor.execute(
                "SELECT id FROM students WHERE id = ?",
                (student_id,),
            ).fetchone()
            if not student_row:
                raise StudentNotFoundForScheduleError(f"Student ID {student_id} not found")

            has_room = _has_column(conn, "class_sections", "room")
            has_lecturer = _has_column(conn, "class_sections", "lecturer")
            has_day = _has_column(conn, "class_sections", "day_of_week")
            has_start = _has_column(conn, "class_sections", "start_period")
            has_end = _has_column(conn, "class_sections", "end_period")

            room_expr = "COALESCE(cs.room, '')" if has_room else "''"
            lecturer_expr = "COALESCE(cs.lecturer, '')" if has_lecturer else "''"
            day_expr = "COALESCE(cs.day_of_week, 2)" if has_day else "2"
            start_expr = "COALESCE(cs.start_period, 1)" if has_start else "1"
            end_expr = "COALESCE(cs.end_period, 1)" if has_end else "1"

            placeholders = ",".join("?" for _ in self.ACTIVE_STATUSES)
            sql = f"""
                SELECT
                    e.id AS enrollment_id,
                    cs.id AS section_id,
                    cs.section_code,
                    c.id AS course_id,
                    c.course_code,
                    c.course_name,
                    c.credits,
                    cs.semester,
                    {day_expr} AS day_of_week,
                    {start_expr} AS start_period,
                    {end_expr} AS end_period,
                    {room_expr} AS room,
                    {lecturer_expr} AS lecturer
                FROM enrollments e
                JOIN class_sections cs ON e.section_id = cs.id
                JOIN courses c ON cs.course_id = c.id
                WHERE e.student_id = ?
                  AND UPPER(e.status) IN ({placeholders})
            """
            params: List[Any] = [student_id, *self.ACTIVE_STATUSES]

            if semester is not None and semester.strip():
                sql += " AND cs.semester = ?"
                params.append(semester.strip())

            sql += f" ORDER BY {day_expr} ASC, {start_expr} ASC, c.course_code ASC"

            rows = cursor.execute(sql, params).fetchall()

            items: List[TimetableItem] = []
            total_credits = 0
            estimated_tuition = 0

            for row in rows:
                credits = int(row["credits"])
                day_num = int(row["day_of_week"])
                amount = credits * rate
                total_credits += credits
                estimated_tuition += amount

                items.append(
                    TimetableItem(
                        enrollment_id=int(row["enrollment_id"]),
                        section_id=int(row["section_id"]),
                        section_code=row["section_code"],
                        course_id=int(row["course_id"]),
                        course_code=row["course_code"],
                        course_name=row["course_name"],
                        credits=credits,
                        semester=row["semester"],
                        day_of_week=day_num,
                        day_label=DAY_NAMES.get(day_num, f"Thứ {day_num}"),
                        start_period=int(row["start_period"]),
                        end_period=int(row["end_period"]),
                        room=row["room"],
                        lecturer=row["lecturer"],
                        tuition_amount=amount,
                    )
                )

            return PersonalScheduleTuitionSummary(
                student_id=student_id,
                semester=semester.strip() if (semester and semester.strip()) else None,
                tuition_per_credit=rate,
                total_courses=len(items),
                total_credits=total_credits,
                estimated_tuition=estimated_tuition,
                items=items,
            )
        finally:
            if should_close:
                conn.close()
