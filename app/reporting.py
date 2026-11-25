"""US8: Báo cáo và xuất danh sách sinh viên đăng ký chính thức theo lớp."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from .repository import InMemoryRepository

HEADERS = ("STT", "MSSV", "Họ và tên", "Thời gian đăng ký")


@dataclass(frozen=True)
class ReportRow:
    index: int
    student_id: str
    full_name: str
    registered_at: datetime


@dataclass(frozen=True)
class ClassReport:
    class_id: str
    course_code: str
    course_name: str
    lecturer: str
    capacity: int
    rows: tuple[ReportRow, ...]

    @property
    def total(self) -> int:
        return len(self.rows)

    @property
    def fill_rate(self) -> float:
        """Tỷ lệ lấp đầy (0..1); 0 nếu lớp chưa đặt sĩ số tối đa."""
        return self.total / self.capacity if self.capacity else 0.0


def build_report(repo: InMemoryRepository, class_id: str) -> ClassReport:
    section = repo.get_class(class_id)
    course = repo.get_course(section.course_code)
    enrollments = sorted(
        repo.registered_enrollments_of_class(class_id), key=lambda e: e.student_id
    )
    rows = tuple(
        ReportRow(i, e.student_id, repo.get_student(e.student_id).full_name, e.registered_at)
        for i, e in enumerate(enrollments, start=1)
    )
    return ClassReport(class_id, course.code, course.name, section.lecturer, section.capacity, rows)


def _safe_cell(value: str) -> str:
    """Chống CSV/Excel formula injection: ô bắt đầu bằng = + - @ bị Excel hiểu là công thức."""
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def _row_values(row: ReportRow) -> list:
    return [
        row.index,
        _safe_cell(row.student_id),
        _safe_cell(row.full_name),
        row.registered_at.strftime("%d/%m/%Y %H:%M"),
    ]


def export_csv(report: ClassReport) -> bytes:
    """CSV UTF-8 có BOM để Excel hiển thị đúng tiếng Việt."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(HEADERS)
    for row in report.rows:
        writer.writerow(_row_values(row))
    return buffer.getvalue().encode("utf-8-sig")


def export_xlsx(report: ClassReport) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Danh sách lớp"

    ws.append([f"Lớp {report.class_id} - {report.course_name} ({report.course_code})"])
    ws["A1"].font = Font(bold=True, size=13)
    ws.append([f"Giảng viên: {report.lecturer}"])
    ws.append([f"Sĩ số: {report.total}/{report.capacity}"])
    ws.append([])
    ws.append(list(HEADERS))
    header_row = ws.max_row
    for cell in ws[header_row]:
        cell.font = Font(bold=True)

    for row in report.rows:
        ws.append(_row_values(row))

    for col, width in enumerate((6, 14, 28, 20), start=1):
        ws.column_dimensions[get_column_letter(col)].width = width

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()
