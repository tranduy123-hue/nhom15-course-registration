import csv
import io
from datetime import datetime

import pytest
from openpyxl import load_workbook

from app.models import Enrollment, EnrollmentStatus, Student
from app.repository import NotFoundError
from app.reporting import HEADERS, build_report, export_csv, export_xlsx


def test_build_report_counts_only_registered(repo):
    repo.add_enrollment(Enrollment("SV002", "INT201-01", EnrollmentStatus.CANCELLED))
    report = build_report(repo, "INT201-01")
    assert report.total == 2
    assert [r.student_id for r in report.rows] == ["SV001", "SV003"]
    assert [r.index for r in report.rows] == [1, 2]
    assert report.capacity == 40
    assert report.fill_rate == pytest.approx(2 / 40)


def test_empty_class_report(repo):
    report = build_report(repo, "INT301-01")
    assert report.total == 0
    assert report.rows == ()


def test_unknown_class(repo):
    with pytest.raises(NotFoundError):
        build_report(repo, "KHONG_CO")


def test_fill_rate_zero_when_no_capacity(repo):
    from dataclasses import replace

    report = build_report(repo, "INT201-01")
    assert replace(report, capacity=0).fill_rate == 0.0


def test_csv_export_utf8_bom_and_content(repo):
    data = export_csv(build_report(repo, "INT201-01"))
    assert data.startswith(b"\xef\xbb\xbf")  # BOM cho Excel
    rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))
    assert tuple(rows[0]) == HEADERS
    assert rows[1][:3] == ["1", "SV001", "Nguyễn Văn An"]
    assert rows[1][3] == "20/11/2026 09:00"
    assert len(rows) == 3


def test_xlsx_export_content(repo):
    data = export_xlsx(build_report(repo, "INT201-01"))
    ws = load_workbook(io.BytesIO(data)).active
    values = [[c.value for c in row] for row in ws.iter_rows()]
    header_idx = next(i for i, r in enumerate(values) if r[0] == "STT")
    assert tuple(values[header_idx]) == HEADERS
    assert values[header_idx + 1][1:3] == ["SV001", "Nguyễn Văn An"]
    assert "Sĩ số: 2/40" in [r[0] for r in values]


@pytest.mark.parametrize("evil", ["=HYPERLINK(\"http://x\")", "+1+1", "-2+3", "@SUM(A1)"])
def test_formula_injection_is_neutralised(repo, evil):
    repo.add_student(Student("SV999", evil))
    repo.add_enrollment(Enrollment("SV999", "INT201-01", registered_at=datetime(2026, 11, 22)))
    report = build_report(repo, "INT201-01")

    csv_rows = list(csv.reader(io.StringIO(export_csv(report).decode("utf-8-sig"))))
    assert csv_rows[-1][2] == "'" + evil

    ws = load_workbook(io.BytesIO(export_xlsx(report))).active
    cell = [c for row in ws.iter_rows() for c in row if c.value == "'" + evil]
    assert cell and cell[0].data_type == "s"  # chuỗi, không phải công thức
