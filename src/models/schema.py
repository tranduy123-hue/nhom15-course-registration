from dataclasses import dataclass
from typing import Optional


@dataclass
class Student:
    student_code: str
    full_name: str
    email: str
    major: str
    academic_year: int
    id: Optional[int] = None


@dataclass
class Course:
    course_code: str
    course_name: str
    credits: int
    department: str
    id: Optional[int] = None


@dataclass
class Prerequisite:
    course_id: int
    prerequisite_course_id: int


@dataclass
class ClassSection:
    section_code: str
    course_id: int
    semester: str
    max_capacity: int
    enrolled_count: int
    day_of_week: int  # 2 (Thứ 2) -> 8 (Chủ nhật)
    start_period: int
    end_period: int
    room: str
    lecturer: str
    id: Optional[int] = None


@dataclass
class Enrollment:
    student_id: int
    section_id: int
    registered_at: str
    status: str = "REGISTERED"  # REGISTERED, CANCELLED, COMPLETED
    id: Optional[int] = None


@dataclass
class AcademicRecord:
    student_id: int
    course_id: int
    grade: float
    is_passed: bool
    id: Optional[int] = None