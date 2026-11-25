"""Mô hình miền (domain) của hệ thống đăng ký môn học."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum


class EnrollmentStatus(str, Enum):
    REGISTERED = "registered"  # đăng ký chính thức
    CANCELLED = "cancelled"  # đã hủy


@dataclass(frozen=True)
class Student:
    id: str  # MSSV
    full_name: str
    completed_courses: frozenset[str] = frozenset()  # mã môn đã hoàn thành (đạt)


@dataclass(frozen=True)
class Course:
    code: str
    name: str
    credits: int
    prerequisites: tuple[str, ...] = ()  # mã các môn tiên quyết


@dataclass(frozen=True)
class ClassSection:
    """Lớp học phần: một môn học mở vào một khung giờ cụ thể."""

    id: str
    course_code: str
    weekday: int  # 2..8 (2 = Thứ Hai, ..., 8 = Chủ Nhật)
    start: time
    end: time
    room: str = ""
    capacity: int = 0
    lecturer: str = ""
    week_start: int = 1  # tuần bắt đầu học
    week_end: int = 15  # tuần kết thúc

    def __post_init__(self) -> None:
        if not 2 <= self.weekday <= 8:
            raise ValueError("weekday phải nằm trong khoảng 2..8")
        if self.start >= self.end:
            raise ValueError("Giờ bắt đầu phải trước giờ kết thúc")
        if self.week_start > self.week_end:
            raise ValueError("week_start phải <= week_end")


@dataclass
class Enrollment:
    student_id: str
    class_id: str
    status: EnrollmentStatus = EnrollmentStatus.REGISTERED
    registered_at: datetime = field(default_factory=datetime.now)
