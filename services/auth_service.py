import os
import logging
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from repositories.user_repository import UserRepository
from utils.db_manager import User

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.secret_key = os.getenv("JWT_SECRET_KEY", "finsight-jwt-secret-change-in-production")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.expiration_minutes = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    def create_access_token(self, user_id: int, email: str) -> str:
        expires = datetime.now(timezone.utc) + timedelta(minutes=self.expiration_minutes)
        payload = {"sub": str(user_id), "email": email, "exp": expires}
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_access_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"JWT decode failed: {e}")
            return None

    def register(self, full_name: str, email: str, password: str) -> dict:
        existing = self.user_repo.find_by_email(email)
        if existing:
            raise ValueError("Email already registered.")
        password_hash = self.hash_password(password)
        user = self.user_repo.create(full_name, email, password_hash)
        token = self.create_access_token(user.id, user.email)
        logger.info(f"User registered: {email}")
        return {
            "access_token": token,
            "user_id": user.id,
            "name": user.full_name,
            "email": user.email,
        }

    def login(self, email: str, password: str) -> dict:
        password_hash = self.user_repo.get_password_hash(email)
        if not password_hash:
            logger.warning(f"Login failed for unknown email: {email}")
            raise ValueError("Invalid email or password.")
        if not self.verify_password(password, password_hash):
            logger.warning(f"Login failed for: {email}")
            raise ValueError("Invalid email or password.")
        user = self.user_repo.find_by_email(email)
        token = self.create_access_token(user.id, user.email)
        logger.info(f"User logged in: {email}")
        return {
            "access_token": token,
            "user_id": user.id,
            "name": user.full_name,
            "email": user.email,
        }

    def get_current_user(self, token: str) -> Optional[User]:
        payload = self.decode_access_token(token)
        if payload is None:
            return None
        user_id = int(payload.get("sub"))
        return self.user_repo.find_by_id(user_id)
