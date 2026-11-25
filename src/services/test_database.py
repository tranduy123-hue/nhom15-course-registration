import sqlite3
import pytest

from src.services.connection import DatabaseManager
from src.services.schema import (
    AcademicRecord,
    ClassSection,
    Course,
    Enrollment,
    Prerequisite,
    Student,
)


@pytest.fixture
def db_manager(tmp_path) -> DatabaseManager:
    """Khởi tạo CSDL SQLite tạm thời trên ổ đĩa cho mỗi test case."""
    db_file = tmp_path / "test_dkmh.db"
    manager = DatabaseManager(db_file)
    manager.init_schema()
    return manager


def test_schema_creates_all_six_tables(db_manager: DatabaseManager) -> None:
    """Kiểm tra khởi tạo đầy đủ 6 bảng quan hệ theo chuẩn ERD."""
    expected_tables = {
        "students",
        "courses",
        "prerequisites",
        "class_sections",
        "enrollments",
        "academic_records",
    }
    conn = db_manager.get_connection()
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        actual_tables = {row["name"] for row in cursor.fetchall()}
        assert actual_tables == expected_tables
    finally:
        conn.close()


def test_foreign_keys_pragma_enabled(db_manager: DatabaseManager) -> None:
    """Kiểm tra PRAGMA foreign_keys = ON được bật tự động."""
    conn = db_manager.get_connection()
    try:
        fk_status = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        assert fk_status == 1
    finally:
        conn.close()


def test_insert_valid_relational_data(db_manager: DatabaseManager) -> None:
    """Kiểm tra chèn dữ liệu hợp lệ xuyên suốt cả 6 bảng và ánh xạ qua Data Classes."""
    student = Student(
        student_code="25S1020032",
        full_name="Phan Văn Hào",
        email="hao.pv@hueuni.edu.vn",
        major="Sư phạm Tin học",
        academic_year=2025,
    )
    course_base = Course(
        course_code="TIN101",
        course_name="Nhập môn Lập trình",
        credits=3,
        department="Khoa Tin học",
    )
    course_adv = Course(
        course_code="TIN202",
        course_name="Cơ sở dữ liệu",
        credits=3,
        department="Khoa Tin học",
    )

    with db_manager.transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO students (student_code, full_name, email, major, academic_year)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                student.student_code,
                student.full_name,
                student.email,
                student.major,
                student.academic_year,
            ),
        )
        student.id = cur.lastrowid

        cur = conn.execute(
            "INSERT INTO courses (course_code, course_name, credits, department) VALUES (?, ?, ?, ?)",
            (course_base.course_code, course_base.course_name, course_base.credits, course_base.department),
        )
        course_base.id = cur.lastrowid

        cur = conn.execute(
            "INSERT INTO courses (course_code, course_name, credits, department) VALUES (?, ?, ?, ?)",
            (course_adv.course_code, course_adv.course_name, course_adv.credits, course_adv.department),
        )
        course_adv.id = cur.lastrowid

        prereq = Prerequisite(course_id=course_adv.id, prerequisite_course_id=course_base.id)
        conn.execute(
            "INSERT INTO prerequisites (course_id, prerequisite_course_id) VALUES (?, ?)",
            (prereq.course_id, prereq.prerequisite_course_id),
        )

        record = AcademicRecord(
            student_id=student.id,
            course_id=course_base.id,
            grade=8.5,
            is_passed=True,
        )
        conn.execute(
            "INSERT INTO academic_records (student_id, course_id, grade, is_passed) VALUES (?, ?, ?, ?)",
            (record.student_id, record.course_id, record.grade, int(record.is_passed)),
        )

        section = ClassSection(
            section_code="TIN202.01",
            course_id=course_adv.id,
            semester="2026-1",
            max_capacity=50,
            enrolled_count=1,
            day_of_week=3,
            start_period=1,
            end_period=3,
            room="A204",
            lecturer="TS. Nguyễn Văn A",
        )
        cur = conn.execute(
            """
            INSERT INTO class_sections (
                section_code, course_id, semester, max_capacity, enrolled_count,
                day_of_week, start_period, end_period, room, lecturer
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                section.section_code,
                section.course_id,
                section.semester,
                section.max_capacity,
                section.enrolled_count,
                section.day_of_week,
                section.start_period,
                section.end_period,
                section.room,
                section.lecturer,
            ),
        )
        section.id = cur.lastrowid

        enrollment = Enrollment(
            student_id=student.id,
            section_id=section.id,
            registered_at="2026-11-24T20:00:00",
            status="REGISTERED",
        )
        conn.execute(
            "INSERT INTO enrollments (student_id, section_id, registered_at, status) VALUES (?, ?, ?, ?)",
            (enrollment.student_id, enrollment.section_id, enrollment.registered_at, enrollment.status),
        )

    conn = db_manager.get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) FROM enrollments").fetchone()
        assert row[0] == 1
    finally:
        conn.close()


def test_foreign_key_constraint_violation(db_manager: DatabaseManager) -> None:
    """Kiểm tra từ chối chèn dữ liệu khi khóa ngoại không tồn tại."""
    with pytest.raises(sqlite3.IntegrityError):
        with db_manager.transaction() as conn:
            conn.execute(
                """
                INSERT INTO class_sections (
                    section_code, course_id, semester, max_capacity, enrolled_count,
                    day_of_week, start_period, end_period, room, lecturer
                ) VALUES ('ERR01', 9999, '2026-1', 40, 0, 2, 1, 3, 'B101', 'GV B')
                """
            )


def test_unique_constraints_and_acid_rollback(db_manager: DatabaseManager) -> None:
    """Kiểm tra ràng buộc UNIQUE và cơ chế ROLLBACK giao dịch ACID khi gặp lỗi."""
    with db_manager.transaction() as conn:
        conn.execute(
            "INSERT INTO students (student_code, full_name, email, major, academic_year) VALUES (?, ?, ?, ?, ?)",
            ("SV001", "Nguyễn Văn An", "an@hueuni.edu.vn", "CNTT", 2025),
        )

    # Giao dịch chứa 1 lệnh hợp lệ và 1 lệnh vi phạm UNIQUE email -> phải rollback toàn bộ
    with pytest.raises(sqlite3.IntegrityError):
        with db_manager.transaction() as conn:
            conn.execute(
                "INSERT INTO students (student_code, full_name, email, major, academic_year) VALUES (?, ?, ?, ?, ?)",
                ("SV002", "Trần Thị Bình", "binh@hueuni.edu.vn", "CNTT", 2025),
            )
            # Trùng email 'an@hueuni.edu.vn'
            conn.execute(
                "INSERT INTO students (student_code, full_name, email, major, academic_year) VALUES (?, ?, ?, ?, ?)",
                ("SV003", "Lê Văn Cường", "an@hueuni.edu.vn", "CNTT", 2025),
            )

    # Xác nhận SV002 không bị lưu dở dang (Atomicity)
    conn = db_manager.get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        assert count == 1
    finally:
        conn.close()