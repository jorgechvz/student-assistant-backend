"""Password hasher module"""

import bcrypt


class PasswordHasher:
    """Class to handle password hashing and verification."""

    def hash(self, password: str) -> str:
        """Hash a plaintext password."""
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a hashed password."""
        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
