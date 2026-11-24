"""
Authentication and Role-Based Access Control (RBAC) Service.
Task: DKMH-5 (US1)
Author: Trần Duy (tranduy123-hue)
"""
import hashlib
import hmac
import secrets
import sqlite3
from typing import Dict, Any, List, Optional


class AuthenticationError(Exception):
    """Base exception for authentication failures."""
    pass


class UserNotFoundError(AuthenticationError):
    """Raised when the username is not found in the database."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when the provided password is incorrect."""
    pass


class UserAlreadyExistsError(Exception):
    """Raised when attempting to register a username that already exists."""
    pass


class AuthorizationError(Exception):
    """Raised when a user attempts an action outside their granted role."""
    pass


def hash_password(password: str, iterations: int = 100_000) -> str:
    """
    Hash a password securely using PBKDF2 with SHA-256 and a random cryptographic salt.
    Format returned: salt_hex$hash_hex
    """
    if not password:
        raise ValueError("Password cannot be empty")
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations
    )
    return f"{salt}${key.hex()}"


def verify_password(password: str, stored_hash: str, iterations: int = 100_000) -> bool:
    """
    Verify password against stored salt$hash using constant-time comparison.
    """
    if not password or not stored_hash or '$' not in stored_hash:
        return False
    try:
        salt, expected_hash = stored_hash.split('$', 1)
        actual_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        ).hex()
        return hmac.compare_digest(actual_hash, expected_hash)
    except Exception:
        return False


class AuthService:
    """
    Service handling user registration, credential authentication, and RBAC authorization.
    """

    ALLOWED_ROLES = {"STUDENT", "ADMIN", "ACADEMIC_AFFAIR"}

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.init_auth_table()

    def init_auth_table(self) -> None:
        """Create users table if it does not exist."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('STUDENT', 'ADMIN', 'ACADEMIC_AFFAIR')),
                full_name TEXT NOT NULL,
                student_code TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def register_user(
        self,
        username: str,
        password: str,
        role: str,
        full_name: str,
        student_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register a new user account with hashed password.
        """
        username = username.strip().lower()
        if not username:
            raise ValueError("Username cannot be empty")
        if role not in self.ALLOWED_ROLES:
            raise ValueError(f"Invalid role: {role}. Allowed: {self.ALLOWED_ROLES}")

        pwd_hash = hash_password(password)
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, full_name, student_code)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username, pwd_hash, role, full_name, student_code)
            )
            self.conn.commit()
            user_id = cursor.lastrowid
            return {
                "id": user_id,
                "username": username,
                "role": role,
                "full_name": full_name,
                "student_code": student_code
            }
        except sqlite3.IntegrityError:
            raise UserAlreadyExistsError(f"Username '{username}' already exists")

    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user credentials and return sanitized user profile.
        """
        username = username.strip().lower()
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, username, password_hash, role, full_name, student_code
            FROM users
            WHERE username = ?
            """,
            (username,)
        )
        row = cursor.fetchone()
        if not row:
            raise UserNotFoundError(f"User '{username}' does not exist")

        user_id, uname, stored_hash, role, full_name, student_code = row

        if not verify_password(password, stored_hash):
            raise InvalidCredentialsError("Incorrect password provided")

        return {
            "id": user_id,
            "username": uname,
            "role": role,
            "full_name": full_name,
            "student_code": student_code
        }

    @staticmethod
    def authorize(user: Dict[str, Any], allowed_roles: List[str]) -> bool:
        """
        Check whether the authenticated user has permission to access the resource.
        """
        user_role = user.get("role")
        if user_role not in allowed_roles:
            raise AuthorizationError(
                f"Permission denied. Role '{user_role}' cannot access this resource. Allowed: {allowed_roles}"
            )
        return True
