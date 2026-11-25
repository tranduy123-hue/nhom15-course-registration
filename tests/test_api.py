"""Test API end-to-end. Tự bỏ qua nếu chưa cài fastapi/httpx."""

import io

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402
from openpyxl import load_workbook  # noqa: E402

from app.main import app, get_repo  # noqa: E402
from app.repository import seed_repository  # noqa: E402


@pytest.fixture
def client():
    repo = seed_repository()
    app.dependency_overrides[get_repo] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_validate_ok(client):
    r = client.post("/api/enrollments/validate", json={"student_id": "SV003", "class_id": "INT301-01"})
    assert r.status_code == 200 and r.json() == {"ok": True, "violations": []}


def test_enroll_rejected_missing_prerequisite(client):
    r = client.post("/api/enrollments", json={"student_id": "SV002", "class_id": "INT201-01"})
    assert r.status_code == 422
    assert r.json()["detail"]["violations"][0]["code"] == "PREREQUISITE_NOT_MET"


def test_enroll_success_then_duplicate(client):
    body = {"student_id": "SV003", "class_id": "INT301-01"}
    assert client.post("/api/enrollments", json=body).status_code == 201
    again = client.post("/api/enrollments", json=body)
    assert again.status_code == 422
    assert again.json()["detail"]["violations"][0]["code"] == "ALREADY_REGISTERED"


def test_enroll_unknown_student_404(client):
    r = client.post("/api/enrollments", json={"student_id": "X", "class_id": "INT201-01"})
    assert r.status_code == 404


def test_report_json(client):
    r = client.get("/api/classes/INT201-01/enrollments/report")
    assert r.status_code == 200
    assert r.json()["total"] == 2


def test_export_csv_and_xlsx(client):
    csv_r = client.get("/api/classes/INT201-01/enrollments/export?format=csv")
    assert csv_r.status_code == 200
    assert "attachment" in csv_r.headers["content-disposition"]
    assert "SV001" in csv_r.content.decode("utf-8-sig")

    x_r = client.get("/api/classes/INT201-01/enrollments/export?format=xlsx")
    assert x_r.status_code == 200
    assert load_workbook(io.BytesIO(x_r.content)).active.max_row >= 6


def test_export_invalid_format_422(client):
    assert client.get("/api/classes/INT201-01/enrollments/export?format=pdf").status_code == 422


def test_export_unknown_class_404(client):
    assert client.get("/api/classes/NOPE/enrollments/export").status_code == 404
