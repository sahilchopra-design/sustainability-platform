"""
Rate Limiting Middleware — P0 Security Item
============================================
Protects expensive calculation endpoints from abuse and DDoS.
Uses a sliding-window in-memory counter (no Redis required for MVP).

Tiers:
  - /api/v1/calculate*, /api/v1/cdm-tools/*/calculate, /api/v1/ecl*, /api/v1/pcaf*
    -> 30 requests / minute per IP (heavy compute)
  - POST /api/* general mutation endpoints
    -> 60 requests / minute per IP
  - GET /api/*
    -> 120 requests / minute per IP

Returns HTTP 429 with Retry-After header when exceeded.
"""

import time
import threading
from collections import defaultdict
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


# ---------------------------------------------------------------------------
#  Configuration
# ---------------------------------------------------------------------------

WINDOW_SECONDS = 60

# Path prefix -> (max_requests_per_window, label)
RATE_TIERS = [
    # Tier 1: Heavy calculation endpoints (most restrictive)
    (
        [
            "/api/v1/calculate",
            "/api/v1/cdm-tools/",
            "/api/v1/ecl-climate/",
            "/api/v1/pcaf/",
            "/api/v1/monte-carlo/",
            "/api/v1/scenario-analysis/",
            "/api/v1/carbon/calculate",
            "/api/v1/cbam/calculate",
            "/api/v1/nature-risk/calculate",
            "/api/v1/stranded/calculate",
            "/api/v1/valuation/calculate",
        ],
        30,
        "calculation",
    ),
    # Tier 2: POST/PUT/PATCH/DELETE mutation endpoints
    (
        None,  # matched by method, not path
        60,
        "mutation",
    ),
    # Tier 3: GET endpoints (least restrictive)
    (
        None,
        120,
        "read",
    ),
]

# Paths that are never rate-limited
EXEMPT_PATHS = frozenset(
    [
        "/api/health",
        "/api/auth/me",
        "/docs",
        "/openapi.json",
        "/redoc",
    ]
)


# ---------------------------------------------------------------------------
#  In-Memory Sliding Window Store
# ---------------------------------------------------------------------------

class _SlidingWindowStore:
    """Thread-safe sliding-window counter per (IP, tier) key."""

    def __init__(self):
        self._lock = threading.Lock()
        # key -> list of timestamps
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.monotonic()

    def is_allowed(self, key: str, limit: int, window: int = WINDOW_SECONDS) -> tuple[bool, int, float]:
        """
        Returns (allowed: bool, remaining: int, retry_after: float).
        """
        now = time.monotonic()
        cutoff = now - window

        with self._lock:
            # Prune expired entries
            bucket = self._buckets[key]
            bucket[:] = [t for t in bucket if t > cutoff]

            if len(bucket) >= limit:
                # Earliest entry in window -> retry after it expires
                retry_after = bucket[0] - cutoff
                return False, 0, max(retry_after, 1.0)

            bucket.append(now)
            remaining = limit - len(bucket)
            return True, remaining, 0.0

    def cleanup(self):
        """Periodically remove stale keys (call every ~5 min)."""
        now = time.monotonic()
        cutoff = now - WINDOW_SECONDS * 2

        with self._lock:
            stale = [k for k, v in self._buckets.items() if not v or v[-1] < cutoff]
            for k in stale:
                del self._buckets[k]
            self._last_cleanup = now


_store = _SlidingWindowStore()


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For behind proxy."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _match_tier(path: str, method: str) -> tuple[int, str]:
    """Return (limit, tier_label) for this request."""
    path_lower = path.lower()

    # Exempt paths
    if path_lower in EXEMPT_PATHS:
        return 0, "exempt"

    # Tier 1: calculation endpoints (any method)
    calc_prefixes = RATE_TIERS[0][0]
    for prefix in calc_prefixes:
        if path_lower.startswith(prefix):
            return RATE_TIERS[0][1], RATE_TIERS[0][2]

    # Tier 2: mutation methods
    if method in ("POST", "PUT", "PATCH", "DELETE"):
        return RATE_TIERS[1][1], RATE_TIERS[1][2]

    # Tier 3: reads
    return RATE_TIERS[2][1], RATE_TIERS[2][2]


# ---------------------------------------------------------------------------
#  Middleware
# ---------------------------------------------------------------------------

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that enforces per-IP rate limits
    using a sliding-window in-memory counter.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        limit, tier = _match_tier(path, method)

        # Exempt
        if tier == "exempt" or limit == 0:
            return await call_next(request)

        ip = _get_client_ip(request)
        key = f"{ip}:{tier}"

        allowed, remaining, retry_after = _store.is_allowed(key, limit)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded ({tier} tier: {limit} req/{WINDOW_SECONDS}s). "
                              f"Retry after {retry_after:.0f}s.",
                    "tier": tier,
                    "limit": limit,
                    "window_seconds": WINDOW_SECONDS,
                },
                headers={
                    "Retry-After": str(int(retry_after)),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                },
            )

        response = await call_next(request)

        # Attach rate-limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        # Periodic cleanup (every ~300s)
        if time.monotonic() - _store._last_cleanup > 300:
            _store.cleanup()

        return response
