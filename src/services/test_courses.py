import pytest
from src.services.connection import DatabaseManager
from src.services.course_service import (
    get_open_sections,
    get_section_detail,
    search_courses,
)


@pytest.fixture
def seeded_db(tmp_path) -> DatabaseManager:
    """Khởi tạo CSDL SQLite mẫu có dữ liệu môn học và lớp học phần."""
    db_file = tmp_path / "test_catalog.db"
    manager = DatabaseManager(db_file)
    manager.init_schema()

    with manager.transaction() as conn:
        conn.executemany(
            """
            INSERT INTO courses (id, course_code, course_name, credits, department)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (1, "TIN101", "Nhập môn Lập trình Python", 3, "CNTT"),
                (2, "TIN202", "Cơ sở Dữ liệu Quan hệ", 3, "CNTT"),
                (3, "TOAN101", "Đại số Tuyến tính", 3, "Toán - Tin"),
            ],
        )

        conn.executemany(
            """
            INSERT INTO class_sections (
                id, section_code, course_id, semester, lecturer,
                schedule, room, max_capacity, enrolled_count, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    10,
                    "TIN101.01",
                    1,
                    "2026-1",
                    "TS. Nguyễn Văn An",
                    "Thứ 2 (Tiết 1-3)",
                    "P.A201",
                    40,
                    25,
                    "OPEN",
                ),
                (
                    11,
                    "TIN101.02",
                    1,
                    "2026-1",
                    "ThS. Trần Thị Bình",
                    "Thứ 4 (Tiết 4-6)",
                    "P.B105",
                    30,
                    30,
                    "OPEN",
                ),
                (
                    12,
                    "TOAN101.01",
                    3,
                    "2026-1",
                    "PGS. Lê Văn Cường",
                    "Thứ 5 (Tiết 1-3)",
                    "P.C302",
                    50,
                    10,
                    "OPEN",
                ),
                (
                    13,
                    "TIN202.01",
                    2,
                    "2025-2",
                    "TS. Phạm Minh Dũng",
                    "Thứ 6 (Tiết 7-9)",
                    "P.A102",
                    40,
                    15,
                    "OPEN",
                ),
                (
                    14,
                    "TIN202.02",
                    2,
                    "2026-1",
                    "TS. Phạm Minh Dũng",
                    "Thứ 7 (Tiết 1-3)",
                    "P.A103",
                    40,
                    0,
                    "CLOSED",
                ),
            ],
        )

    return manager


def test_search_courses_by_code(seeded_db: DatabaseManager):
    results = search_courses(seeded_db, "TIN101")
    assert len(results) == 1
    assert results[0]["course_code"] == "TIN101"
    assert results[0]["course_name"] == "Nhập môn Lập trình Python"


def test_search_courses_by_name_case_insensitive(seeded_db: DatabaseManager):
    # Tìm kiếm gần đúng và không phân biệt chữ hoa/thường
    results = search_courses(seeded_db, "cơ sở dữ liệu")
    assert len(results) == 1
    assert results[0]["course_code"] == "TIN202"

    results_upper = search_courses(seeded_db, "LẬP TRÌNH")
    assert len(results_upper) == 1
    assert results_upper[0]["course_code"] == "TIN101"


def test_get_open_sections_by_semester_and_department(seeded_db: DatabaseManager):
    # Lọc tất cả lớp đang OPEN trong học kỳ 2026-1 (bỏ qua 2025-2 và lớp CLOSED)
    sections_2026_1 = get_open_sections(seeded_db, semester="2026-1")
    assert len(sections_2026_1) == 3
    section_codes = {s["section_code"] for s in sections_2026_1}
    assert section_codes == {"TIN101.01", "TIN101.02", "TOAN101.01"}

    # Lọc thêm theo khoa CNTT
    cntt_sections = get_open_sections(seeded_db, semester="2026-1", department="cntt")
    assert len(cntt_sections) == 2
    assert all(s["department"] == "CNTT" for s in cntt_sections)


def test_remaining_slots_and_is_full_flag(seeded_db: DatabaseManager):
    # Lớp còn chỗ (40 - 25 = 15 chỗ trống -> is_full = False)
    sec_available = get_section_detail(seeded_db, 10)
    assert sec_available is not None
    assert sec_available["max_capacity"] == 40
    assert sec_available["enrolled_count"] == 25
    assert sec_available["remaining_slots"] == 15
    assert sec_available["is_full"] is False
    assert sec_available["lecturer"] == "TS. Nguyễn Văn An"
    assert sec_available["schedule"] == "Thứ 2 (Tiết 1-3)"
    assert sec_available["room"] == "P.A201"

    # Lớp đã đủ sĩ số (30 - 30 = 0 chỗ trống -> is_full = True)
    sec_full = get_section_detail(seeded_db, 11)
    assert sec_full is not None
    assert sec_full["remaining_slots"] == 0
    assert sec_full["is_full"] is True

    # Lớp không tồn tại
    assert get_section_detail(seeded_db, 9999) 