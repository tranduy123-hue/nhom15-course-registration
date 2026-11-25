"""Kho dữ liệu in-memory (dùng cho Sprint đầu; thay bằng DB ở sprint sau)."""

from __future__ import annotations

from datetime import datetime, time

from .models import ClassSection, Course, Enrollment, EnrollmentStatus, Student


class NotFoundError(LookupError):
    """Không tìm thấy sinh viên / môn học / lớp học phần."""


class InMemoryRepository:
    def __init__(self) -> None:
        self._students: dict[str, Student] = {}
        self._courses: dict[str, Course] = {}
        self._classes: dict[str, ClassSection] = {}
        self._enrollments: list[Enrollment] = []

    # --- thêm dữ liệu ---
    def add_student(self, student: Student) -> None:
        self._students[student.id] = student

    def add_course(self, course: Course) -> None:
        self._courses[course.code] = course

    def add_class(self, section: ClassSection) -> None:
        self._classes[section.id] = section

    def add_enrollment(self, enrollment: Enrollment) -> None:
        self._enrollments.append(enrollment)

    # --- truy vấn ---
    def get_student(self, student_id: str) -> Student:
        try:
            return self._students[student_id]
        except KeyError:
            raise NotFoundError(f"Không tìm thấy sinh viên '{student_id}'") from None

    def get_course(self, code: str) -> Course:
        try:
            return self._courses[code]
        except KeyError:
            raise NotFoundError(f"Không tìm thấy môn học '{code}'") from None

    def get_class(self, class_id: str) -> ClassSection:
        try:
            return self._classes[class_id]
        except KeyError:
            raise NotFoundError(f"Không tìm thấy lớp học phần '{class_id}'") from None

    def registered_classes_of(self, student_id: str) -> list[ClassSection]:
        return [
            self._classes[e.class_id]
            for e in self._enrollments
            if e.student_id == student_id and e.status is EnrollmentStatus.REGISTERED
        ]

    def registered_enrollments_of_class(self, class_id: str) -> list[Enrollment]:
        return [
            e
            for e in self._enrollments
            if e.class_id == class_id and e.status is EnrollmentStatus.REGISTERED
        ]


def seed_repository() -> InMemoryRepository:
    """Dữ liệu mẫu để chạy thử và demo."""
    repo = InMemoryRepository()

    repo.add_course(Course("INT101", "Nhập môn lập trình", 3))
    repo.add_course(Course("INT201", "Cấu trúc dữ liệu", 3, ("INT101",)))
    repo.add_course(Course("INT301", "Cơ sở dữ liệu", 3, ("INT201",)))
    repo.add_course(Course("MAT101", "Giải tích 1", 3))

    repo.add_student(Student("SV001", "Nguyễn Văn An", frozenset({"INT101"})))
    repo.add_student(Student("SV002", "Trần Thị Bình", frozenset()))
    repo.add_student(Student("SV003", "Lê Minh Châu", frozenset({"INT101", "INT201"})))

    repo.add_class(
        ClassSection("INT201-01", "INT201", 2, time(7, 0), time(9, 30), "A101", 40, "TS. Phạm Văn D")
    )
    repo.add_class(
        ClassSection("MAT101-01", "MAT101", 2, time(8, 0), time(10, 0), "B202", 60, "ThS. Hoàng Thị E")
    )
    repo.add_class(
        ClassSection("INT301-01", "INT301", 4, time(13, 0), time(15, 30), "A102", 40, "TS. Vũ Văn G")
    )

    repo.add_enrollment(
        Enrollment("SV001", "INT201-01", registered_at=datetime(2026, 11, 20, 9, 0))
    )
    repo.add_enrollment(
        Enrollment("SV003", "INT201-01", registered_at=datetime(2026, 11, 20, 9, 5))
    )
    return repo
