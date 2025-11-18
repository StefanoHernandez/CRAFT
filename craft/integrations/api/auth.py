"""Authentication and API key management."""

import secrets
from typing import Optional, Dict
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel


class APIKey(BaseModel):
    """API key model."""

    key: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    rate_limit: Optional[int] = None  # requests per minute
    is_active: bool = True


class APIKeyManager:
    """Manage API keys for authentication."""

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize API key manager.

        Args:
            master_key: Optional master API key for admin access
        """
        self.keys: Dict[str, APIKey] = {}
        self.master_key = master_key

        # Add master key if provided
        if master_key:
            self.keys[master_key] = APIKey(
                key=master_key,
                name="master",
                created_at=datetime.utcnow(),
                is_active=True,
            )

    def create_key(
        self,
        name: str,
        expires_in_days: Optional[int] = None,
        rate_limit: Optional[int] = None,
    ) -> str:
        """
        Create a new API key.

        Args:
            name: Key name/description
            expires_in_days: Optional expiration in days
            rate_limit: Optional rate limit (requests per minute)

        Returns:
            Generated API key
        """
        key = f"craft_{secrets.token_urlsafe(32)}"

        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        self.keys[key] = APIKey(
            key=key,
            name=name,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            rate_limit=rate_limit,
            is_active=True,
        )

        return key

    def validate_key(self, key: str) -> bool:
        """
        Validate an API key.

        Args:
            key: API key to validate

        Returns:
            True if valid, False otherwise
        """
        if key not in self.keys:
            return False

        api_key = self.keys[key]

        # Check if active
        if not api_key.is_active:
            return False

        # Check expiration
        if api_key.expires_at and datetime.utcnow() > api_key.expires_at:
            api_key.is_active = False
            return False

        return True

    def revoke_key(self, key: str) -> bool:
        """
        Revoke an API key.

        Args:
            key: API key to revoke

        Returns:
            True if revoked, False if not found
        """
        if key in self.keys:
            self.keys[key].is_active = False
            return True
        return False

    def get_key_info(self, key: str) -> Optional[APIKey]:
        """Get API key information."""
        return self.keys.get(key)

    def list_keys(self) -> list[APIKey]:
        """List all API keys."""
        return list(self.keys.values())


# Security scheme
security = HTTPBearer()


def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security),
    key_manager: Optional[APIKeyManager] = None,
) -> str:
    """
    Verify API key from request.

    Args:
        credentials: HTTP authorization credentials
        key_manager: API key manager instance

    Returns:
        Validated API key

    Raises:
        HTTPException: If key is invalid
    """
    if not key_manager:
        # No key manager, allow all requests (development mode)
        return "dev_key"

    api_key = credentials.credentials

    if not key_manager.validate_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return api_key
