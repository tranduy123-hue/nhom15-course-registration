"""US4: Tự động kiểm tra điều kiện tiên quyết và trùng lịch học."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import ClassSection, Student
from .repository import InMemoryRepository

PREREQUISITE_NOT_MET = "PREREQUISITE_NOT_MET"
SCHEDULE_CONFLICT = "SCHEDULE_CONFLICT"
ALREADY_REGISTERED = "ALREADY_REGISTERED"


@dataclass(frozen=True)
class Violation:
    code: str
    message: str
    related: tuple[str, ...] = ()  # mã môn tiên quyết còn thiếu / id lớp bị trùng


@dataclass(frozen=True)
class ValidationResult:
    violations: tuple[Violation, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return not self.violations


def classes_overlap(a: ClassSection, b: ClassSection) -> bool:
    """Hai lớp trùng lịch khi cùng thứ, giao nhau về giờ học và về tuần học."""
    if a.weekday != b.weekday:
        return False
    if a.week_start > b.week_end or b.week_start > a.week_end:
        return False
    return a.start < b.end and b.start < a.end


def check_prerequisites(
    student: Student, section: ClassSection, repo: InMemoryRepository
) -> list[Violation]:
    course = repo.get_course(section.course_code)
    missing = tuple(c for c in course.prerequisites if c not in student.completed_courses)
    if not missing:
        return []
    return [
        Violation(
            PREREQUISITE_NOT_MET,
            f"Chưa hoàn thành môn tiên quyết: {', '.join(missing)}",
            missing,
        )
    ]


def check_schedule_conflicts(
    section: ClassSection, registered: list[ClassSection]
) -> list[Violation]:
    violations: list[Violation] = []
    for other in registered:
        if other.id == section.id:
            continue
        if classes_overlap(section, other):
            violations.append(
                Violation(
                    SCHEDULE_CONFLICT,
                    f"Trùng lịch với lớp {other.id} "
                    f"(Thứ {other.weekday}, {other.start:%H:%M}-{other.end:%H:%M})",
                    (other.id,),
                )
            )
    return violations


def validate_enrollment(
    repo: InMemoryRepository, student_id: str, class_id: str
) -> ValidationResult:
    """Kiểm tra sinh viên có được đăng ký lớp hay không.

    Ném NotFoundError nếu sinh viên / lớp / môn học không tồn tại.
    """
    student = repo.get_student(student_id)
    section = repo.get_class(class_id)
    registered = repo.registered_classes_of(student_id)

    if any(r.id == section.id for r in registered):
        return ValidationResult(
            (Violation(ALREADY_REGISTERED, f"Đã đăng ký lớp {section.id} trước đó", (section.id,)),)
        )

    violations = check_prerequisites(student, section, repo)
    violations += check_schedule_conflicts(section, registered)
    return ValidationResult(tuple(violations))
