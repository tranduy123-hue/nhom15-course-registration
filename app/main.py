"""API FastAPI cho US4 (kiểm tra đăng ký) và US8 (báo cáo/xuất danh sách lớp)."""

from __future__ import annotations

import re
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from pydantic import BaseModel

from .models import Enrollment
from .repository import InMemoryRepository, NotFoundError, seed_repository
from .reporting import build_report, export_csv, export_xlsx
from .validation import ValidationResult, validate_enrollment

app = FastAPI(title="Đăng ký môn học", version="0.1.0")
_repo = seed_repository()


def get_repo() -> InMemoryRepository:
    return _repo


class EnrollmentRequest(BaseModel):
    student_id: str
    class_id: str


def _violations_payload(result: ValidationResult) -> list[dict]:
    return [
        {"code": v.code, "message": v.message, "related": list(v.related)}
        for v in result.violations
    ]


def _validate_or_404(repo: InMemoryRepository, req: EnrollmentRequest) -> ValidationResult:
    try:
        return validate_enrollment(repo, req.student_id, req.class_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------- US4 ----------
@app.post("/api/enrollments/validate")
def validate(req: EnrollmentRequest, repo: InMemoryRepository = Depends(get_repo)) -> dict:
    """Chỉ kiểm tra, không ghi dữ liệu."""
    result = _validate_or_404(repo, req)
    return {"ok": result.ok, "violations": _violations_payload(result)}


@app.post("/api/enrollments", status_code=201)
def enroll(req: EnrollmentRequest, repo: InMemoryRepository = Depends(get_repo)) -> dict:
    """Đăng ký lớp; hệ thống tự từ chối nếu thiếu tiên quyết hoặc trùng lịch."""
    result = _validate_or_404(repo, req)
    if not result.ok:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Yêu cầu đăng ký bị từ chối",
                "violations": _violations_payload(result),
            },
        )
    repo.add_enrollment(Enrollment(req.student_id, req.class_id))
    return {"student_id": req.student_id, "class_id": req.class_id, "status": "registered"}


# ---------- US8 ----------
@app.get("/api/classes/{class_id}/enrollments/report")
def class_report(class_id: str, repo: InMemoryRepository = Depends(get_repo)) -> dict:
    try:
        report = build_report(repo, class_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "class_id": report.class_id,
        "course_code": report.course_code,
        "course_name": report.course_name,
        "lecturer": report.lecturer,
        "capacity": report.capacity,
        "total": report.total,
        "fill_rate": round(report.fill_rate, 4),
        "students": [
            {
                "index": r.index,
                "student_id": r.student_id,
                "full_name": r.full_name,
                "registered_at": r.registered_at.isoformat(),
            }
            for r in report.rows
        ],
    }


@app.get("/api/classes/{class_id}/enrollments/export")
def class_export(
    class_id: str,
    format: Literal["csv", "xlsx"] = Query("csv"),
    repo: InMemoryRepository = Depends(get_repo),
) -> Response:
    try:
        report = build_report(repo, class_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", class_id)
    if format == "csv":
        content, media = export_csv(report), "text/csv; charset=utf-8"
    else:
        content = export_xlsx(report)
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return Response(
        content=content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="lop_{safe_name}.{format}"'},
    )
