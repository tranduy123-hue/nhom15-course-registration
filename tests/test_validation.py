from datetime import datetime, time

import pytest

from app.models import ClassSection, Enrollment
from app.repository import NotFoundError
from app.validation import (
    ALREADY_REGISTERED,
    PREREQUISITE_NOT_MET,
    SCHEDULE_CONFLICT,
    classes_overlap,
    validate_enrollment,
)


def test_ok_when_prerequisite_done_and_no_conflict(repo):
    # SV003 đã học INT101, INT201 -> được học INT301 (Thứ 4, không trùng gì)
    result = validate_enrollment(repo, "SV003", "INT301-01")
    assert result.ok
    assert result.violations == ()


def test_reject_missing_prerequisite(repo):
    # SV002 chưa học INT101 nên không được học INT201
    result = validate_enrollment(repo, "SV002", "INT201-01")
    assert not result.ok
    assert result.violations[0].code == PREREQUISITE_NOT_MET
    assert result.violations[0].related == ("INT101",)


def test_reject_schedule_conflict(repo):
    # SV001 đang học INT201-01 (Thứ 2, 07:00-09:30); MAT101-01 (Thứ 2, 08:00-10:00) trùng
    result = validate_enrollment(repo, "SV001", "MAT101-01")
    assert [v.code for v in result.violations] == [SCHEDULE_CONFLICT]
    assert result.violations[0].related == ("INT201-01",)


def test_report_both_violations_at_once(repo):
    repo.add_enrollment(Enrollment("SV002", "MAT101-01", registered_at=datetime(2026, 11, 21)))
    result = validate_enrollment(repo, "SV002", "INT201-01")
    codes = {v.code for v in result.violations}
    assert codes == {PREREQUISITE_NOT_MET, SCHEDULE_CONFLICT}


def test_reject_duplicate_enrollment(repo):
    result = validate_enrollment(repo, "SV001", "INT201-01")
    assert [v.code for v in result.violations] == [ALREADY_REGISTERED]


def test_cancelled_enrollment_does_not_cause_conflict(repo):
    from app.models import EnrollmentStatus

    repo.add_enrollment(Enrollment("SV002", "MAT101-01", EnrollmentStatus.CANCELLED))
    repo.add_student(repo.get_student("SV002"))
    result = validate_enrollment(repo, "SV002", "MAT101-01")
    assert result.ok


def test_unknown_student_or_class(repo):
    with pytest.raises(NotFoundError):
        validate_enrollment(repo, "KHONG_CO", "INT201-01")
    with pytest.raises(NotFoundError):
        validate_enrollment(repo, "SV001", "KHONG_CO")


def _cls(cid, weekday, start, end, w1=1, w2=15):
    return ClassSection(cid, "X", weekday, start, end, week_start=w1, week_end=w2)


def test_touching_time_is_not_overlap():
    a = _cls("a", 2, time(7, 0), time(9, 0))
    b = _cls("b", 2, time(9, 0), time(11, 0))
    assert not classes_overlap(a, b)


def test_different_weekday_is_not_overlap():
    assert not classes_overlap(_cls("a", 2, time(7), time(9)), _cls("b", 3, time(7), time(9)))


def test_different_weeks_is_not_overlap():
    a = _cls("a", 2, time(7), time(9), 1, 7)
    b = _cls("b", 2, time(7), time(9), 8, 15)
    assert not classes_overlap(a, b)


def test_invalid_class_time_rejected():
    with pytest.raises(ValueError):
        _cls("bad", 2, time(10), time(9))
