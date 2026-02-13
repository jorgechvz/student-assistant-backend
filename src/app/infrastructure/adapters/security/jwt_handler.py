"""JWT handler module"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from app.infrastructure.config.config import get_settings


class JWTHandler:
    """Class to handle JWT operations like creation and verification."""

    def __init__(self):
        self.settings = get_settings()

    def create_access_token(
        self, user_id: str, additional_claims: Optional[dict] = None
    ) -> str:
        """Create a JWT access token."""
        expires_delta = timedelta(minutes=self.settings.jwt_access_token_expire_minutes)
        expire = datetime.now(timezone.utc) + expires_delta

        to_encode = {
            "sub": user_id,
            "type": "access",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }

        if additional_claims:
            to_encode.update(additional_claims)

        return jwt.encode(
            to_encode,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

    def create_refresh_token(self, user_id: str) -> str:
        """Create a JWT refresh token."""
        expires_delta = timedelta(days=self.settings.jwt_refresh_token_expire_days)
        expire = datetime.now(timezone.utc) + expires_delta

        to_encode = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }

        return jwt.encode(
            to_encode,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

    def decode_token(self, token: str) -> dict:
        """Decode and verify a JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )
            return payload
        except jwt.ExpiredSignatureError as exc:
            raise ValueError("Token has expired") from exc
        except jwt.InvalidTokenError as exc:
            raise ValueError("Invalid token") from exc

    def verify_token(self, token: str, token_type: str) -> dict:
        """Verify the type of the JWT token."""
        payload = self.decode_token(token)
        if payload.get("type") != token_type:
            raise ValueError(f"Invalid token type: expected {token_type}")
        return payload
