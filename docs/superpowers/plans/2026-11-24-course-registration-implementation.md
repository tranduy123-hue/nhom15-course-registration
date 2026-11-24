# Hệ Thống Đăng Ký Môn Học (CRMS) - Kế Hoạch Triển Khai Kỹ Thuật (Implementation Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng khung kiến trúc chuẩn, môi trường kiểm thử và các module nghiệp vụ cốt lõi (xác thực, kiểm tra tiên quyết, phát hiện trùng lịch, đăng ký học phần an toàn giao dịch) cho Hệ thống Quản lý và Đăng ký Môn học (Nhóm 15 - CNPM).

**Architecture:** Ứng dụng mô hình kiến trúc phân tầng 3-Tier Layered Architecture với Repository Pattern. Tầng dịch vụ (Services) bao bọc toàn bộ quy tắc nghiệp vụ (Business Rules), tầng dữ liệu sử dụng SQLite với giao dịch ACID và row-level constraints để xử lý an toàn đồng thời, tầng trình diễn cung cấp RESTful API và giao diện web trực quan.

**Tech Stack:** Python 3.10+, FastAPI / Uvicorn, SQLite3 (ACID Transactions), Pytest (TDD / Unit Testing), Git / GitHub Actions CI, Jira Software (`DKMH`).

---

## Danh Mục Phân Công Triển Khai Theo Jira

| Mã Task Jira | Tên Nhiệm Vụ | Thành viên thực hiện | Phạm vi Module / Tệp |
|:---|:---|:---|:---|
| `DKMH-1` | Setup Git Repository, CI Workflow & Chuẩn hóa tài liệu | **Trần Duy** | `.github/workflows/ci.yml`, `README.md`, `.gitignore` |
| `DKMH-2` | Nghiên cứu kiến trúc & Xây dựng mô hình dữ liệu CSDL | **Phan Văn Hào** | `src/models/schema.py`, `src/database/connection.py` |
| `DKMH-3` | Chuẩn hóa Product Backlog & Quy tắc nghiệp vụ kiểm tra | **Lê Quân Bảo** | `src/services/prerequisite_service.py`, `src/services/conflict_service.py` |
| `DKMH-4` | Thiết lập môi trường local & Bộ kiểm thử baseline TDD | **Phan Thanh Thịnh** | `src/services/student_service.py`, `tests/conftest.py`, `tests/test_baseline.py` |
| `DKMH-5` | Xác thực đăng nhập & Phân quyền người dùng (RBAC) | **Trần Duy** | `src/services/auth_service.py`, `tests/test_auth.py` |
| `DKMH-7` | Đăng ký lớp học phần an toàn giao dịch (Atomic Enrollment) | **Trần Duy** | `src/services/registration_service.py`, `tests/test_registration.py` |

---

## Cấu Trúc Thư Mục Dự Án (Project File Layout)

```
nhom15-course-registration/
├── .github/
│   └── workflows/
│       └── ci.yml                          # GitHub Actions CI pipeline
├── docs/
│   └── superpowers/
│       ├── specs/
│       │   └── 2026-11-24-course-registration-design.md
│       └── plans/
│           └── 2026-11-24-course-registration-implementation.md
├── src/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py                   # Quản lý kết nối & Schema DDL
│   ├── models/
│   │   ├── __init__.py
│   │   └── schema.py                       # Data classes: Student, Course, Section, Enrollment
│   └── services/
│       ├── __init__.py
│       ├── auth_service.py                 # Xác thực & phân quyền (Duy)
│       ├── prerequisite_service.py         # Kiểm tra môn tiên quyết (Bảo)
│       ├── conflict_service.py             # Kiểm tra trùng thời khóa biểu (Bảo)
│       ├── registration_service.py         # Giao dịch đăng ký môn an toàn (Duy)
│       └── student_service.py              # Tra cứu TKB, hủy môn, tính học phí (Thịnh)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                         # Fixtures dữ liệu mẫu SQLite in-memory
│   ├── test_baseline.py                    # Kiểm tra môi trường & kết nối CSDL
│   ├── test_auth.py                        # Kiểm thử xác thực & mã hóa mật khẩu
│   ├── test_prerequisites.py               # Kiểm thử quy tắc môn tiên quyết
│   ├── test_conflicts.py                   # Kiểm thử phát hiện trùng lịch học
│   ├── test_registration.py                # Kiểm thử đăng ký & xử lý quá sĩ số
│   └── test_student_services.py            # Kiểm thử hủy môn & tính học phí
├── requirements.txt                        # Danh sách thư viện phụ thuộc
├── pytest.ini                              # Cấu hình Pytest
└── README.md                               # Hướng dẫn cài đặt & vận hành
```

---

## Chi Tiết Các Bước Triển Khai (Bite-Sized Tasks)

### Task 1: [DKMH-1] Khởi tạo Cấu trúc Dự án, CI Workflow và Tài liệu Hướng dẫn
**Thành viên phụ trách:** Trần Duy (`tranduy123-hue`)  
**Files:**
- Create: `requirements.txt`
- Create: `pytest.ini`
- Create: `.github/workflows/ci.yml`
- Modify: `README.md`

- [ ] **Step 1: Khởi tạo file dependencies `requirements.txt` và cấu hình test `pytest.ini`**
  - Khai báo các thư viện cần thiết: `pytest>=8.0.0`, `pytest-cov>=4.1.0`.
- [ ] **Step 2: Tạo quy trình CI tự động `.github/workflows/ci.yml`**
  - Chạy GitHub Actions trên push và pull request vào nhánh `main`.
  - Tự động cài đặt Python 3.11, tải dependencies và chạy `pytest -v`.
- [ ] **Step 3: Cập nhật `README.md` chuẩn hóa thông tin môn học**
  - Bổ sung tên đề tài, bảng thành viên nhóm, link Jira Board `DKMH`, hướng dẫn clone và chạy test.
- [ ] **Step 4: Commit thay đổi với author Trần Duy**
  ```bash
  git add requirements.txt pytest.ini .github/ README.md
  git commit -m "[DKMH-1] chore: setup project skeleton, CI workflow, and team documentation"
  ```

---

### Task 2: [DKMH-2] Xây dựng Lớp Mô hình Dữ liệu và Quản lý Cơ sở Dữ liệu
**Thành viên phụ trách:** Phan Văn Hào (`phanvanhao1103-create`)  
**Files:**
- Create: `src/models/schema.py`
- Create: `src/database/connection.py`
- Test: `tests/test_database.py`

- [ ] **Step 1: Viết test kiểm thử khởi tạo CSDL và tạo các bảng**
  - Tạo `tests/test_database.py` kiểm tra các bảng: `students`, `courses`, `prerequisites`, `class_sections`, `enrollments`, `academic_records`.
- [ ] **Step 2: Chạy test để xác nhận kiểm thử thất bại (FAIL)**
  - Chạy: `pytest tests/test_database.py`
  - Kết quả mong đợi: FAIL do chưa có module `src/database/connection.py`.
- [ ] **Step 3: Cài đặt `src/database/connection.py` và `src/models/schema.py`**
  - Thiết lập SQLite kết nối in-memory và file persistent, tự động bật `PRAGMA foreign_keys = ON;`.
  - Định nghĩa DDL tạo đầy đủ các bảng dữ liệu với ràng buộc khóa chính, khóa ngoại và unique index.
- [ ] **Step 4: Chạy lại test để xác nhận kiểm thử thành công (PASS)**
  - Chạy: `pytest tests/test_database.py`
  - Kết quả mong đợi: Tất cả các bảng được tạo thành công, Foreign Key hoạt động chuẩn.
- [ ] **Step 5: Commit thay đổi với author Phan Văn Hào**
  ```bash
  git add src/models/ src/database/ tests/test_database.py
  git commit -m "[DKMH-2] feat: implement relational database schema and SQLite connection manager"
  ```

---

### Task 3: [DKMH-4] Thiết lập Môi trường Local, Fixtures Kiểm thử và Dịch vụ Sinh viên
**Thành viên phụ trách:** Phan Thanh Thịnh (`phanthanhthinhptt27-cmd`)  
**Files:**
- Create: `tests/conftest.py`
- Create: `src/services/student_service.py`
- Test: `tests/test_student_services.py`

- [ ] **Step 1: Viết test kiểm thử tra cứu TKB cá nhân, hủy đăng ký môn học và tính học phí**
  - Viết các ca kiểm thử: Hủy lớp học phần đã đăng ký (giảm `enrolled_count`), sinh viên xem danh sách môn đã đăng ký, tính tổng học phí dựa trên số tín chỉ.
- [ ] **Step 2: Chạy test để xác nhận kiểm thử thất bại (FAIL)**
  - Chạy: `pytest tests/test_student_services.py`
  - Kết quả mong đợi: FAIL do chưa có `StudentService`.
- [ ] **Step 3: Cài đặt `tests/conftest.py` và `src/services/student_service.py`**
  - Cung cấp fixtures tạo dữ liệu mẫu: Sinh viên CNTT, các môn học cơ sở & chuyên ngành, lớp học phần mở.
  - Cài đặt hàm `cancel_enrollment()`, `get_student_schedule()`, `calculate_tuition()`.
- [ ] **Step 4: Chạy lại test để xác nhận kiểm thử thành công (PASS)**
  - Chạy: `pytest tests/test_student_services.py`
  - Kết quả mong đợi: PASS 100%.
- [ ] **Step 5: Commit thay đổi với author Phan Thanh Thịnh**
  ```bash
  git add tests/conftest.py src/services/student_service.py tests/test_student_services.py
  git commit -m "[DKMH-4] feat: setup test fixtures and implement student schedule and cancellation service"
  ```

---

### Task 4: [DKMH-8] Cài đặt Quy tắc Nghiệp vụ Kiểm tra Môn Tiên quyết & Trùng Lịch học
**Thành viên phụ trách:** Lê Quân Bảo (`lequanbaodepzai`)  
**Files:**
- Create: `src/services/prerequisite_service.py`
- Create: `src/services/conflict_service.py`
- Test: `tests/test_prerequisites.py`
- Test: `tests/test_conflicts.py`

- [ ] **Step 1: Viết test kiểm tra điều kiện tiên quyết và phát hiện trùng thời khóa biểu**
  - Case 1: Sinh viên chưa học môn Nhập môn Lập trình -> Không được đăng ký Kỹ thuật Lập trình.
  - Case 2: Sinh viên đã qua môn Nhập môn Lập trình (điểm 7.0) -> Được phép đăng ký Kỹ thuật Lập trình.
  - Case 3: Lớp A học Thứ 2 tiết 1-3, Lớp B học Thứ 2 tiết 3-5 -> Phát hiện trùng lịch (tiết 3).
  - Case 4: Lớp A học Thứ 2 tiết 1-3, Lớp C học Thứ 2 tiết 4-6 -> Không trùng lịch, hợp lệ.
- [ ] **Step 2: Chạy test để xác nhận kiểm thử thất bại (FAIL)**
  - Chạy: `pytest tests/test_prerequisites.py tests/test_conflicts.py`
  - Kết quả mong đợi: FAIL do chưa có code chức năng.
- [ ] **Step 3: Cài đặt `PrerequisiteService` và `ConflictDetectorService`**
  - Cài đặt thuật toán kiểm tra đệ quy môn tiên quyết đối chiếu với bảng `academic_records`.
  - Cài đặt thuật toán kiểm tra giao đoạn thời gian: `has_overlap = (day_A == day_B) and not (end_A < start_B or start_A > end_B)`.
- [ ] **Step 4: Chạy lại test để xác nhận kiểm thử thành công (PASS)**
  - Chạy: `pytest tests/test_prerequisites.py tests/test_conflicts.py`
  - Kết quả mong đợi: PASS toàn bộ các ca kiểm thử biên.
- [ ] **Step 5: Commit thay đổi với author Lê Quân Bảo**
  ```bash
  git add src/services/prerequisite_service.py src/services/conflict_service.py tests/test_prerequisites.py tests/test_conflicts.py
  git commit -m "[DKMH-8] feat: implement prerequisite validation and schedule conflict detection engine"
  ```

---

### Task 5: [DKMH-5] Cài đặt Dịch vụ Xác thực & Phân quyền Người Dùng (RBAC)
**Thành viên phụ trách:** Trần Duy (`tranduy123-hue`)  
**Files:**
- Create: `src/services/auth_service.py`
- Test: `tests/test_auth.py`

- [ ] **Step 1: Viết test kiểm tra đăng nhập sinh viên, quản trị viên và mã hóa mật khẩu an toàn**
  - Case 1: Đăng nhập đúng username/password -> Trả về thông tin user và role (`STUDENT` hoặc `ADMIN`).
  - Case 2: Đăng nhập sai mật khẩu -> Trả về lỗi xác thực `AuthenticationError`.
  - Case 3: Kiểm tra mật khẩu được băm an toàn với salt (PBKDF2/SHA256).
- [ ] **Step 2: Chạy test để xác nhận kiểm thử thất bại (FAIL)**
  - Chạy: `pytest tests/test_auth.py`
  - Kết quả mong đợi: FAIL.
- [ ] **Step 3: Cài đặt `AuthService`**
  - Cài đặt hàm `hash_password()`, `verify_password()`, `authenticate()`, `register_user()`.
- [ ] **Step 4: Chạy lại test để xác nhận kiểm thử thành công (PASS)**
  - Chạy: `pytest tests/test_auth.py`
  - Kết quả mong đợi: PASS.
- [ ] **Step 5: Commit thay đổi với author Trần Duy**
  ```bash
  git add src/services/auth_service.py tests/test_auth.py
  git commit -m "[DKMH-5] feat: implement secure authentication and role-based authorization service"
  ```

---

### Task 6: [DKMH-7] Cài đặt Động cơ Đăng ký Học phần An toàn Giao dịch (Core Registration Engine)
**Thành viên phụ trách:** Trần Duy (`tranduy123-hue`)  
**Files:**
- Create: `src/services/registration_service.py`
- Test: `tests/test_registration.py`

- [ ] **Step 1: Viết test kiểm tra luồng đăng ký học phần tổng hợp và kiểm soát sĩ số**
  - Case 1: Đăng ký thành công khi thỏa mãn điều kiện tiên quyết, không trùng lịch, lớp còn chỗ.
  - Case 2: Từ chối đăng ký khi lớp học phần đã đạt `max_capacity` (sĩ số tối đa).
  - Case 3: Từ chối đăng ký khi sinh viên đã đăng ký một lớp học phần khác của cùng môn học đó.
  - Case 4: Đảm bảo tính toàn vẹn giao dịch (Atomic rollback nếu xảy ra lỗi giữa chừng).
- [ ] **Step 2: Chạy test để xác nhận kiểm thử thất bại (FAIL)**
  - Chạy: `pytest tests/test_registration.py`
  - Kết quả mong đợi: FAIL.
- [ ] **Step 3: Cài đặt `RegistrationService`**
  - Tích hợp `PrerequisiteService`, `ConflictDetectorService` và Database Transaction context manager.
  - Cập nhật số lượng `enrolled_count` nguyên tử (atomic increment).
- [ ] **Step 4: Chạy toàn bộ test suite dự án**
  - Chạy: `pytest -v`
  - Kết quả mong đợi: Toàn bộ test suite pass 100%.
- [ ] **Step 5: Commit thay đổi với author Trần Duy**
  ```bash
  git add src/services/registration_service.py tests/test_registration.py
  git commit -m "[DKMH-7] feat: implement atomic course registration service with capacity protection"
  ```

---

## Tiêu Chí Nghiệm Thu Toàn Diện (End-to-End Verification)

Khi 3 thành viên (`phanvanhao1103-create`, `phanthanhthinhptt27-cmd`, `lequanbaodepzai`) chấp nhận lời mời cộng tác trên GitHub:
1. Thực hiện lần lượt các task theo TDD, kiểm tra bằng lệnh:
   ```bash
   pytest -v --tb=short
   ```
2. Kiểm tra lịch sử Git commit bằng lệnh:
   ```bash
   git log --pretty=format:"%h - %an <%ae> [%ad]: %s" --date=short
   ```
   Đảm bảo tác giả của các commit tương ứng khớp 100% với phân công trên Jira (`DKMH-1` đến `DKMH-12`).
3. Đẩy code lên nhánh `main` của kho lưu trữ GitHub:
   ```bash
   git push origin main
   ```
