from typing import Any, Optional
import sqlite3


def _get_conn(db: Any) -> tuple[sqlite3.Connection, bool]:
    """Hỗ trợ truyền vào DatabaseManager hoặc sqlite3.Connection trực tiếp."""
    if hasattr(db, "get_connection"):
        return db.get_connection(), True
    return db, False


def _format_section_row(row: sqlite3.Row) -> dict[str, Any]:
    """Chuẩn hóa thông tin lớp học phần và tính toán chỗ trống, trạng thái đầy."""
    max_capacity = int(row["max_capacity"])
    enrolled_count = int(row["enrolled_count"])
    remaining_slots = max(0, max_capacity - enrolled_count)

    return {
        "section_id": row["id"],
        "section_code": row["section_code"],
        "course_id": row["course_id"],
        "course_code": row["course_code"],
        "course_name": row["course_name"],
        "credits": row["credits"],
        "department": row["department"],
        "semester": row["semester"],
        "lecturer": row["lecturer"],
        "schedule": row["schedule"],
        "room": row["room"],
        "max_capacity": max_capacity,
        "enrolled_count": enrolled_count,
        "remaining_slots": remaining_slots,
        "is_full": remaining_slots == 0,
        "status": row["status"],
    }


def search_courses(db: Any, keyword: str) -> list[dict[str, Any]]:
    """
    Tìm kiếm danh mục môn học theo mã môn hoặc tên môn (gần đúng, không phân biệt hoa/thường).
    """
    conn, should_close = _get_conn(db)
    try:
        clean_kw = (keyword or "").strip().lower()
        if not clean_kw:
            cursor = conn.execute(
                """
                SELECT id, course_code, course_name, credits, department
                FROM courses
                ORDER BY course_code ASC
                """
            )
        else:
            pattern = f"%{clean_kw}%"
            cursor = conn.execute(
                """
                SELECT id, course_code, course_name, credits, department
                FROM courses
                WHERE LOWER(course_code) LIKE ? OR LOWER(course_name) LIKE ?
                ORDER BY course_code ASC
                """,
                (pattern, pattern),
            )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        if should_close:
            conn.close()


def get_open_sections(
    db: Any, semester: str, department: Optional[str] = None
) -> list[dict[str, Any]]:
    """
    Lấy danh sách các lớp học phần đang mở ('OPEN') theo học kỳ và tùy chọn lọc theo khoa.
    """
    conn, should_close = _get_conn(db)
    try:
        query = """
            SELECT
                cs.id,
                cs.section_code,
                cs.course_id,
                c.course_code,
                c.course_name,
                c.credits,
                c.department,
                cs.semester,
                cs.lecturer,
                cs.schedule,
                cs.room,
                cs.max_capacity,
                cs.enrolled_count,
                cs.status
            FROM class_sections cs
            JOIN courses c ON cs.course_id = c.id
            WHERE cs.semester = ? AND UPPER(cs.status) = 'OPEN'
        """
        params: list[Any] = [semester.strip()]

        if department and department.strip():
            query += " AND LOWER(c.department) = ?"
            params.append(department.strip().lower())

        query += " ORDER BY c.course_code ASC, cs.section_code ASC"

        cursor = conn.execute(query, params)
        return [_format_section_row(row) for row in cursor.fetchall()]
    finally:
        if should_close:
            conn.close()


def get_section_detail(db: Any, section_id: int) -> Optional[dict[str, Any]]:
    """
    Truy vấn thông tin chi tiết một lớp học phần theo section_id.
    Trả về None nếu không tìm thấy.
    """
    conn, should_close = _get_conn(db)
    try:
        cursor = conn.execute(
            """
            SELECT
                cs.id,
                cs.section_code,
                cs.course_id,
                c.course_code,
                c.course_name,
                c.credits,
                c.department,
                cs.semester,
                cs.lecturer,
                cs.schedule,
                cs.room,
                cs.max_capacity,
                cs.enrolled_count,
                cs.status
            FROM class_sections cs
            JOIN courses c ON cs.course_id = c.id
            WHERE cs.id = ?
            """,
            (section_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _format_section_row(row)
    finally:
        if should_close:
            conn.close()
def create_section(
    db: Any,
    course_id: int,
    section_code: str,
    max_capacity: int,
    day: str,
    start: int,
    end: int,
    room: str,
    lecturer: str,
    semester: str = "2026-1",
) -> dict[str, Any]:
    """
    Mở một lớp học phần mới ('OPEN') với thông tin giảng viên, phòng học, lịch học và sĩ số tối đa.
    """
    if max_capacity <= 0:
        raise ValueError("Sĩ số tối đa (max_capacity) phải lớn hơn 0.")
    if start <= 0 or end < start:
        raise ValueError("Tiết bắt đầu và tiết kết thúc không hợp lệ.")

    schedule_str = f"{day.strip()} (Tiết {start}-{end})"
    clean_code = section_code.strip()
    clean_room = room.strip()
    clean_lecturer = lecturer.strip()
    clean_semester = semester.strip()

    conn, should_close = _get_conn(db)
    try:
        # Kiểm tra môn học có tồn tại không
        course_row = conn.execute(
            "SELECT id FROM courses WHERE id = ?", (course_id,)
        ).fetchone()
        if course_row is None:
            raise ValueError(f"Không tìm thấy môn học với course_id={course_id}.")

        cursor = conn.execute(
            """
            INSERT INTO class_sections (
                section_code,
                course_id,
                semester,
                lecturer,
                schedule,
                room,
                max_capacity,
                enrolled_count,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'OPEN')
            """,
            (
                clean_code,
                course_id,
                clean_semester,
                clean_lecturer,
                schedule_str,
                clean_room,
                max_capacity,
            ),
        )
        conn.commit()
        new_section_id = cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        if should_close:
            conn.close()

    detail = get_section_detail(db, new_section_id)
    assert detail is not None
    return detail


def update_section_capacity(
    db: Any, section_id: int, new_capacity: int
) -> dict[str, Any]:
    """
    Điều chỉnh sĩ số tối đa của lớp học phần.
    Chặn cập nhật nếu new_capacity nhỏ hơn số sinh viên đã đăng ký (enrolled_count).
    """
    if new_capacity <= 0:
        raise ValueError("Sĩ số tối đa mới phải lớn hơn 0.")

    conn, should_close = _get_conn(db)
    try:
        row = conn.execute(
            "SELECT id, enrolled_count FROM class_sections WHERE id = ?",
            (section_id,),
        ).fetchone()

        if row is None:
            raise ValueError(f"Không tìm thấy lớp học phần với section_id={section_id}.")

        enrolled_count = int(row["enrolled_count"])
        if new_capacity < enrolled_count:
            raise ValueError(
                f"Không thể giảm sĩ số tối đa ({new_capacity}) thấp hơn số sinh viên đã đăng ký ({enrolled_count})."
            )

        conn.execute(
            "UPDATE class_sections SET max_capacity = ? WHERE id = ?",
            (new_capacity, section_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if should_close:
            conn.close()

    detail = get_section_detail(db, section_id)
    assert detail is not None
    return detail