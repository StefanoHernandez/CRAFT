"""Rate limiting for API endpoints."""

import time
from typing import Dict, Optional
from collections import defaultdict, deque
from fastapi import HTTPException, status


class RateLimiter:
    """
    Simple in-memory rate limiter.

    For production, consider using Redis-based rate limiting.
    """

    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute per key
        """
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute in seconds
        self.requests: Dict[str, deque] = defaultdict(deque)

    def check_rate_limit(self, key: str, limit: Optional[int] = None) -> bool:
        """
        Check if request is within rate limit.

        Args:
            key: Identifier (e.g., API key or IP address)
            limit: Optional custom limit for this key

        Returns:
            True if within limit, False otherwise
        """
        now = time.time()
        max_requests = limit or self.requests_per_minute

        # Clean old requests outside the time window
        request_times = self.requests[key]
        while request_times and request_times[0] < now - self.window_size:
            request_times.popleft()

        # Check if within limit
        if len(request_times) >= max_requests:
            return False

        # Add current request
        request_times.append(now)
        return True

    def get_remaining(self, key: str, limit: Optional[int] = None) -> int:
        """
        Get remaining requests for a key.

        Args:
            key: Identifier
            limit: Optional custom limit

        Returns:
            Number of remaining requests
        """
        max_requests = limit or self.requests_per_minute
        now = time.time()

        # Clean old requests
        request_times = self.requests[key]
        while request_times and request_times[0] < now - self.window_size:
            request_times.popleft()

        return max(0, max_requests - len(request_times))

    def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        if key in self.requests:
            del self.requests[key]


def rate_limit_dependency(
    api_key: str,
    rate_limiter: RateLimiter,
    limit: Optional[int] = None,
) -> None:
    """
    FastAPI dependency for rate limiting.

    Args:
        api_key: API key from authentication
        rate_limiter: Rate limiter instance
        limit: Optional custom limit

    Raises:
        HTTPException: If rate limit exceeded
    """
    if not rate_limiter.check_rate_limit(api_key, limit):
        remaining = rate_limiter.get_remaining(api_key, limit)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={
                "X-RateLimit-Remaining": str(remaining),
                "Retry-After": "60",
            },
        )
