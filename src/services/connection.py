import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Union


SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_code TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    major TEXT NOT NULL,
    academic_year INTEGER NOT NULL CHECK (academic_year >= 2000)
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL UNIQUE,
    course_name TEXT NOT NULL,
    credits INTEGER NOT NULL CHECK (credits > 0),
    department TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prerequisites (
    course_id INTEGER NOT NULL,
    prerequisite_course_id INTEGER NOT NULL,
    PRIMARY KEY (course_id, prerequisite_course_id),
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (prerequisite_course_id) REFERENCES courses(id) ON DELETE RESTRICT,
    CHECK (course_id != prerequisite_course_id)
);

CREATE TABLE IF NOT EXISTS class_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_code TEXT NOT NULL,
    course_id INTEGER NOT NULL,
    semester TEXT NOT NULL,
    max_capacity INTEGER NOT NULL CHECK (max_capacity > 0),
    enrolled_count INTEGER NOT NULL DEFAULT 0 CHECK (enrolled_count >= 0 AND enrolled_count <= max_capacity),
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 2 AND 8),
    start_period INTEGER NOT NULL CHECK (start_period BETWEEN 1 AND 12),
    end_period INTEGER NOT NULL CHECK (end_period BETWEEN 1 AND 12 AND end_period >= start_period),
    room TEXT NOT NULL,
    lecturer TEXT NOT NULL,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE RESTRICT,
    UNIQUE (section_code, semester)
);

CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    registered_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'REGISTERED' CHECK (status IN ('REGISTERED', 'CANCELLED', 'COMPLETED')),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES class_sections(id) ON DELETE RESTRICT,
    UNIQUE (student_id, section_id)
);

CREATE TABLE IF NOT EXISTS academic_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    grade REAL NOT NULL CHECK (grade >= 0.0 AND grade <= 10.0),
    is_passed INTEGER NOT NULL CHECK (is_passed IN (0, 1)),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE RESTRICT,
    UNIQUE (student_id, course_id)
);
"""


class DatabaseManager:
    """Quản lý kết nối SQLite, khởi tạo schema và đảm bảo giao dịch ACID."""

    def __init__(self, db_path: Union[str, Path] = "course_registration.db") -> None:
        self.db_path = str(db_path)

    def get_connection(self) -> sqlite3.Connection:
        """Tạo kết nối SQLite mới và luôn bật kiểm tra khóa ngoại."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager cung cấp giao dịch ACID (tự động COMMIT hoặc ROLLBACK)."""
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        """Khởi tạo toàn bộ 6 bảng quan hệ và các ràng buộc."""
        with self.transaction() as conn:
            conn.executescript(SCHEMA_DDL)