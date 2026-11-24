"""
Unit Tests for Authentication and Role-Based Authorization Service.
Task: DKMH-5 (US1)
Author: Trần Duy (tranduy123-hue)
"""
import sqlite3
import pytest
from src.services.auth_service import (
    AuthService,
    hash_password,
    verify_password,
    AuthenticationError,
    UserNotFoundError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    AuthorizationError
)


@pytest.fixture
def auth_service():
    """Provides an in-memory SQLite connection with AuthService initialized."""
    conn = sqlite3.connect(":memory:")
    service = AuthService(conn)
    yield service
    conn.close()


class TestPasswordHashing:
    def test_hash_creates_salted_format(self):
        hashed = hash_password("Secret123")
        assert "$" in hashed
        salt, key = hashed.split("$")
        assert len(salt) == 32
        assert len(key) == 64

    def test_verify_password_correct(self):
        password = "SecurePassword2026!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("CorrectPassword")
        assert verify_password("WrongPassword", hashed) is False

    def test_verify_password_malformed_hash(self):
        assert verify_password("Password", "invalid_hash_string") is False
        assert verify_password("", "salt$hash") is False

    def test_hash_empty_password_raises_value_error(self):
        with pytest.raises(ValueError):
            hash_password("")


class TestAuthServiceUserManagement:
    def test_register_student_success(self, auth_service):
        user = auth_service.register_user(
            username="sv_tranduy",
            password="Password123@",
            role="STUDENT",
            full_name="Trần Duy",
            student_code="20T1020001"
        )
        assert user["id"] is not None
        assert user["username"] == "sv_tranduy"
        assert user["role"] == "STUDENT"
        assert user["full_name"] == "Trần Duy"
        assert user["student_code"] == "20T1020001"

    def test_register_duplicate_username_fails(self, auth_service):
        auth_service.register_user("admin_user", "AdminPass1", "ADMIN", "Quản Trị Viên")
        with pytest.raises(UserAlreadyExistsError):
            auth_service.register_user("admin_user", "AdminPass2", "ADMIN", "Quản Trị Viên 2")

    def test_register_invalid_role_fails(self, auth_service):
        with pytest.raises(ValueError, match="Invalid role"):
            auth_service.register_user("hacker", "pass", "SUPER_HACKER", "Unknown")


class TestAuthServiceAuthentication:
    def test_authenticate_student_success(self, auth_service):
        auth_service.register_user(
            username="duy_student",
            password="MySecretPassword!",
            role="STUDENT",
            full_name="Trần Duy",
            student_code="20T1020001"
        )
        profile = auth_service.authenticate("duy_student", "MySecretPassword!")
        assert profile["username"] == "duy_student"
        assert profile["role"] == "STUDENT"
        assert profile["student_code"] == "20T1020001"

    def test_authenticate_admin_success(self, auth_service):
        auth_service.register_user(
            username="daotao_admin",
            password="AdminRootPassword!",
            role="ADMIN",
            full_name="Phòng Đào Tạo"
        )
        profile = auth_service.authenticate("daotao_admin", "AdminRootPassword!")
        assert profile["role"] == "ADMIN"

    def test_authenticate_wrong_password_raises_invalid_credentials(self, auth_service):
        auth_service.register_user("student_user", "RealPass", "STUDENT", "Sinh Viên")
        with pytest.raises(InvalidCredentialsError):
            auth_service.authenticate("student_user", "WrongPass")

    def test_authenticate_nonexistent_user_raises_user_not_found(self, auth_service):
        with pytest.raises(UserNotFoundError):
            auth_service.authenticate("ghost_user", "AnyPassword")


class TestAuthServiceAuthorizationRBAC:
    def test_authorize_allowed_role(self):
        user = {"username": "admin", "role": "ADMIN"}
        assert AuthService.authorize(user, allowed_roles=["ADMIN", "ACADEMIC_AFFAIR"]) is True

    def test_authorize_denied_role_raises_authorization_error(self):
        student_user = {"username": "duy", "role": "STUDENT"}
        with pytest.raises(AuthorizationError):
            AuthService.authorize(student_user, allowed_roles=["ADMIN"])
