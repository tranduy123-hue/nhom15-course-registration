# Hệ Thống Quản Lý Và Đăng Ký Môn Học (CRMS)
## Course Registration and Management System

[![CI Pipeline](https://github.com/tranduy123-hue/nhom15-course-registration/actions/workflows/ci.yml/badge.svg)](https://github.com/tranduy123-hue/nhom15-course-registration/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Testing](https://img.shields.io/badge/tested%20with-pytest-yellow)](https://pytest.org/)
[![Agile Scrum](https://img.shields.io/badge/methodology-Scrum-orange)](https://duygk45.atlassian.net/browse/DKMH)
[![Jira Board](https://img.shields.io/badge/Jira-DKMH%20Board-0052CC?logo=jira)](https://duygk45.atlassian.net/jira/software/projects/DKMH/boards)

---

## 1. Giới Thiệu Dự Án

Dự án **Hệ Thống Quản Lý Và Đăng Ký Môn Học (CRMS)** được thực hiện trong khuôn khổ học phần **Công nghệ phần mềm (Software Engineering) - Suất 2** dưới sự hướng dẫn của **Thầy Long Tran**.

Hệ thống giải quyết bài toán cốt lõi của đào tạo theo học chế tín chỉ:
- **Đăng ký học phần trực tuyến an toàn:** Đảm bảo tính toàn vẹn dữ liệu (ACID Transactions), ngăn ngừa vượt quá sĩ số tối đa khi nhiều sinh viên cùng đăng ký đồng thời (Race Condition Protection).
- **Kiểm soát điều kiện học vụ:** Tự động kiểm tra môn tiên quyết (Prerequisites), giới hạn số tín chỉ và phát hiện trùng lịch học (Schedule Conflict Detection).
- **Quản lý học vụ & thời khóa biểu:** Cho phép sinh viên tra cứu thời khóa biểu cá nhân, ước tính học phí, hủy đăng ký học phần trong thời hạn; cho phép quản trị viên mở lớp và trích xuất danh sách sinh viên.

---

## 2. Danh Sách Thành Viên & Bảng Phân Công Nhiệm Vụ

| STT | Họ và Tên | Vai trò | GitHub Username | Jira Account ID | Phân công chính |
|:---:|:---|:---:|:---|:---|:---|
| 1 | **Trần Duy** | **Nhóm trưởng** | [`tranduy123-hue`](https://github.com/tranduy123-hue) | `712020:1884e774` | Setup Git Repo, CI/CD, Xác thực (US1), Động cơ đăng ký an toàn (US3) |
| 2 | **Phan Văn Hào** | Thành viên | [`phanvanhao1103-create`](https://github.com/phanvanhao1103-create) | `712020:5f217dbc` | Thiết kế kiến trúc, CSDL ERD, Tra cứu môn học (US2), Quản lý lớp HP (US7) |
| 3 | **Lê Quân Bảo** | Thành viên | [`lequanbaodepzai`](https://github.com/lequanbaodepzai) | `712020:36740f29` | Chuẩn hóa Product Backlog, Kiểm tra tiên quyết & trùng lịch (US4), Báo cáo SV (US8) |
| 4 | **Phan Thanh Thịnh** | Thành viên | [`phanthanhthinhptt27-cmd`](https://github.com/phanthanhthinhptt27-cmd) | `712020:63b97d05` | Môi trường test baseline, Hủy môn học (US5), Thời khóa biểu & học phí (US6) |

---

## 3. Quản Lý Dự Án Theo Scrum (Jira Space `DKMH`)

- **Jira Project URL:** [https://duygk45.atlassian.net/browse/DKMH](https://duygk45.atlassian.net/browse/DKMH)
- **Jira Board URL:** [https://duygk45.atlassian.net/jira/software/projects/DKMH/boards](https://duygk45.atlassian.net/jira/software/projects/DKMH/boards)

### Sprint 0 (Khởi tạo, kiến trúc & chuẩn bị môi trường - 10 SP):
- `DKMH-1`: Setup Git Repository trên GitHub và nhóm làm việc (2 SP - Trần Duy)
- `DKMH-2`: Nghiên cứu và thiết kế kiến trúc hệ thống phần mềm (3 SP - Phan Văn Hào)
- `DKMH-3`: Xây dựng và chuẩn hóa Product Backlog theo chuẩn Scrum (3 SP - Lê Quân Bảo)
- `DKMH-4`: Thiết lập môi trường phát triển local và kiểm thử baseline (2 SP - Phan Thanh Thịnh)

### Product Backlog (8 User Stories - 37 SP):
- `DKMH-5` [US1]: Đăng nhập và xác thực phân quyền (3 SP - Must have - Trần Duy)
- `DKMH-6` [US2]: Tra cứu danh mục môn học và danh sách lớp mở (5 SP - Must have - Phan Văn Hào)
- `DKMH-7` [US3]: Đăng ký lớp học phần trực tuyến an toàn & tức thời (8 SP - Must have - Trần Duy)
- `DKMH-8` [US4]: Tự động kiểm tra điều kiện tiên quyết & trùng lịch học (5 SP - Must have - Lê Quân Bảo)
- `DKMH-9` [US5]: Hủy môn học / Rút khỏi lớp học phần đã đăng ký (3 SP - Should have - Phan Thanh Thịnh)
- `DKMH-10` [US6]: Xem thời khóa biểu cá nhân và học phí tạm tính (3 SP - Should have - Phan Thanh Thịnh)
- `DKMH-11` [US7]: Quản lý lớp học phần và thiết lập sĩ số tối đa (5 SP - Should have - Phan Văn Hào)
- `DKMH-12` [US8]: Báo cáo và xuất danh sách sinh viên theo lớp (5 SP - Could have - Lê Quân Bảo)

---

## 4. Cấu Trúc Dự Án (Project Layout)

```
nhom15-course-registration/
├── .github/
│   └── workflows/
│       └── ci.yml                          # GitHub Actions CI pipeline
├── docs/
│   └── superpowers/
│       ├── specs/
│       │   └── 2026-11-24-course-registration-design.md     # Tài liệu thiết kế kiến trúc & Product Backlog
│       └── plans/
│           └── 2026-11-24-course-registration-implementation.md # Kế hoạch triển khai kỹ thuật & TDD
├── src/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py                   # Quản lý kết nối CSDL SQLite
│   ├── models/
│   │   ├── __init__.py
│   │   └── schema.py                       # Data Classes định nghĩa thực thể
│   └── services/
│       ├── __init__.py
│       ├── auth_service.py                 # Xác thực & Phân quyền (US1 - Duy)
│       ├── course_service.py               # Tra cứu & Quản lý lớp HP (US2, US7 - Hào)
│       ├── prerequisite_service.py         # Kiểm tra môn tiên quyết (US4 - Bảo)
│       ├── conflict_service.py             # Phát hiện trùng thời khóa biểu (US4 - Bảo)
│       ├── registration_service.py         # Động cơ đăng ký học phần an toàn (US3 - Duy)
│       ├── student_service.py              # Hủy môn, TKB & Học phí (US5, US6 - Thịnh)
│       └── report_service.py               # Báo cáo thống kê & xuất CSV (US8 - Bảo)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                         # Pytest Fixtures dữ liệu mẫu
│   ├── test_smoke.py                       # Kiểm thử môi trường ban đầu
│   ├── test_auth.py                        # Kiểm thử xác thực
│   └── test_registration.py                # Kiểm thử đăng ký học phần
├── requirements.txt                        # Danh mục thư viện phụ thuộc
├── pytest.ini                              # Cấu hình Pytest
└── README.md
```

---

## 5. Hướng Dẫn Cài Đặt & Chạy Thử Nghiệm Local

### Yêu cầu hệ thống:
- Python 3.10 trở lên.
- Git.

### Các bước cài đặt:

1. **Clone repository về máy:**
   ```bash
   git clone https://github.com/tranduy123-hue/nhom15-course-registration.git
   cd nhom15-course-registration
   ```

2. **Khởi tạo và kích hoạt môi trường ảo:**
   - Trên Linux/macOS:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - Trên Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```

3. **Cài đặt thư viện dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Chạy toàn bộ bộ kiểm thử tự động (Unit Tests):**
   ```bash
   pytest
   ```
   Để hiển thị độ bao phủ mã nguồn (Code Coverage):
   ```bash
   pytest --cov=src --cov-report=term-missing
   ```

---

## 6. Quy Trình Gitflow & Commit Convention

- **Nhánh chính (`main`):** Chứa mã nguồn ổn định, luôn vượt qua kiểm thử CI.
- **Nhánh tính năng (`feature/`):** Mỗi thành viên tạo nhánh riêng tương ứng với mã task Jira:
  - Cú pháp: `feature/DKMH-<mã_task>-<tên_task>` (Ví dụ: `feature/DKMH-2-architecture-db`).
- **Quy chuẩn thông điệp commit (Commit Message Convention):**
  - Cú pháp: `[DKMH-X] <loại>: <mô tả ngắn gọn>`
  - Ví dụ:
    - `[DKMH-1] chore: setup project skeleton, CI workflow, and team documentation`
    - `[DKMH-5] feat: implement secure authentication and role-based authorization service`
    - `[DKMH-7] feat: implement atomic course registration engine with capacity protection`
- **Quy trình đóng góp (Pull Request):**
  - Đẩy nhánh lên GitHub: `git push origin feature/DKMH-X-...`
  - Mở Pull Request vào nhánh `main`.
  - Yêu cầu ít nhất 1 thành viên khác review và phê duyệt (Approve) trước khi merge.
