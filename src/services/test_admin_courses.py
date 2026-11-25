import pytest
from src.services.connection import DatabaseManager
from src.services.course_service import (
    create_section,
    get_section_detail,
    update_section_capacity,
)


@pytest.fixture
def admin_db(tmp_path) -> DatabaseManager:
    """Khởi tạo CSDL SQLite mẫu có sẵn môn học và một lớp học phần đã có sinh viên đăng ký."""
    db_file = tmp_path / "test_admin_courses.db"
    manager = DatabaseManager(db_file)
    manager.init_schema()

    with manager.transaction() as conn:
        conn.execute(
            """
            INSERT INTO courses (id, course_code, course_name, credits, department)
            VALUES (1, 'TIN101', 'Nhập môn Lập trình Python', 3, 'CNTT')
            """
        )
        conn.execute(
            """
            INSERT INTO class_sections (
                id, section_code, course_id, semester, lecturer,
                schedule, room, max_capacity, enrolled_count, status
            )
            VALUES (
                10, 'TIN101.01', 1, '2026-1', 'TS. Nguyễn Văn An',
                'Thứ 2 (Tiết 1-3)', 'P.A201', 40, 25, 'OPEN'
            )
            """
        )

    return manager


def test_create_new_open_section(admin_db: DatabaseManager):
    created = create_section(
        db=admin_db,
        course_id=1,
        section_code="TIN101.03",
        max_capacity=45,
        day="Thứ 3",
        start=4,
        end=6,
        room="P.B202",
        lecturer="ThS. Lê Thị Hoa",
    )

    assert created["section_id"] is not None
    assert created["section_code"] == "TIN101.03"
    assert created["course_code"] == "TIN101"
    assert created["max_capacity"] == 45
    assert created["enrolled_count"] == 0
    assert created["remaining_slots"] == 45
    assert created["is_full"] is False
    assert created["status"] == "OPEN"
    assert created["room"] == "P.B202"
    assert created["lecturer"] == "ThS. Lê Thị Hoa"
    assert created["schedule"] == "Thứ 3 (Tiết 4-6)"


def test_update_section_capacity_increase(admin_db: DatabaseManager):
    updated = update_section_capacity(db=admin_db, section_id=10, new_capacity=60)

    assert updated["section_id"] == 10
    assert updated["max_capacity"] == 60
    assert updated["enrolled_count"] == 25
    assert updated["remaining_slots"] == 35
    assert updated["is_full"] is False


def test_update_section_capacity_below_enrolled_raises_error(admin_db: DatabaseManager):
    # Lớp 10 đang có enrolled_count = 25 -> không được phép giảm xuống 20
    with pytest.raises(ValueError, match="đã đăng ký"):
        update_section_capacity(db=admin_db, section_id=10, new_capacity=20)

    # Xác nhận sĩ số tối đa trong CSDL vẫn giữ nguyên 40
    current = get_section_detail(admin_db, 10)
    assert current is not None
    assert current["max_capacity"] == 40