"""
Connection testing service for data sources.
Attempts a lightweight HTTP probe to verify the source is reachable.
"""
import httpx
import time
import asyncio
from typing import Dict, Any, Optional


TIMEOUT = 10.0
USER_AGENT = "A2-DataHub/1.0 (contact@a2intelligence.com)"


async def test_connection(source: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test connectivity to a data source.
    Returns dict with success, status_code, response_time_ms, error, sample_data.
    """
    access_type = (source.get("access_type") or "").lower()
    base_url = source.get("base_url") or ""
    credentials = source.get("credentials") or {}

    if not base_url or base_url in ("nan", "N/A", "None", ""):
        return {
            "success": False,
            "status_code": None,
            "response_time_ms": None,
            "error": "No base URL configured for this source.",
            "sample_data": None,
        }

    if "scrape" in access_type or "puppeteer" in access_type or "manual" in access_type or "apify" in access_type:
        return {
            "success": True,
            "status_code": None,
            "response_time_ms": None,
            "error": None,
            "sample_data": None,
            "note": f"Access type '{access_type}' — automated connection test not applicable. Verify manually.",
        }

    if "python" in access_type or "library" in access_type:
        return {
            "success": True,
            "status_code": None,
            "response_time_ms": None,
            "error": None,
            "sample_data": None,
            "note": "Python library source — import test not applicable via HTTP probe.",
        }

    # Build test URL
    test_url = _build_test_url(base_url, source)
    if not test_url:
        return {
            "success": False,
            "status_code": None,
            "response_time_ms": None,
            "error": "Cannot construct a test URL from base_url and key_endpoints.",
            "sample_data": None,
        }

    # Build headers
    headers = {"User-Agent": USER_AGENT}
    params: Dict[str, str] = {}

    auth_method = (source.get("auth_method") or "").lower()
    api_key = credentials.get("api_key") or credentials.get("key") or ""

    if "header" in auth_method and api_key:
        header_name = credentials.get("header_name", "Authorization")
        headers[header_name] = api_key
    elif ("param" in auth_method or "query" in auth_method) and api_key:
        param_name = credentials.get("param_name", "api_key")
        params[param_name] = api_key
    elif "bearer" in auth_method and api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    elif "basic" in auth_method:
        client_id = credentials.get("client_id", "")
        client_secret = credentials.get("client_secret", "")
        if client_id and client_secret:
            import base64
            encoded = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

    # Execute probe
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            response = await client.get(test_url, headers=headers, params=params)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        success = response.status_code < 400
        sample = None
        if success and "json" in response.headers.get("content-type", ""):
            try:
                sample = response.json()
                if isinstance(sample, dict):
                    # Truncate large responses
                    sample = {k: v for k, v in list(sample.items())[:5]}
                elif isinstance(sample, list):
                    sample = sample[:2]
            except Exception:
                pass

        return {
            "success": success,
            "status_code": response.status_code,
            "response_time_ms": elapsed_ms,
            "error": None if success else f"HTTP {response.status_code}: {response.reason_phrase}",
            "sample_data": sample,
        }

    except httpx.TimeoutException:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {
            "success": False,
            "status_code": None,
            "response_time_ms": elapsed_ms,
            "error": f"Connection timed out after {TIMEOUT}s",
            "sample_data": None,
        }
    except Exception as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {
            "success": False,
            "status_code": None,
            "response_time_ms": elapsed_ms,
            "error": str(e),
            "sample_data": None,
        }


def _build_test_url(base_url: str, source: Dict[str, Any]) -> Optional[str]:
    """Build a minimal test URL from the source configuration."""
    if not base_url:
        return None
    base_url = base_url.strip().rstrip("/")
    if not base_url.startswith("http"):
        base_url = "https://" + base_url

    endpoints = source.get("key_endpoints") or ""
    if endpoints:
        # Take the first endpoint fragment
        first = endpoints.split(";")[0].split("\n")[0].strip()
        # Extract path (between backticks or first /endpoint)
        import re
        match = re.search(r"`([^`]+)`", first)
        if match:
            path = match.group(1).split("?")[0].strip()
            # Remove param placeholders
            path = re.sub(r"\{[^}]+\}", "test", path)
            return base_url + path
        # Try raw /endpoint
        match = re.search(r"(/[a-zA-Z0-9_/.-]+)", first)
        if match:
            path = match.group(1).split("?")[0]
            return base_url + path

    # Just probe the base URL
    return base_url


async def run_sync(source: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    Lightweight sync simulation — real ingestion connectors would go here.
    Returns stats dict.
    """
    access_type = (source.get("access_type") or "").lower()
    await asyncio.sleep(0.5)  # Simulate work

    return {
        "rows_fetched": 0,
        "rows_inserted": 0,
        "rows_updated": 0,
        "rows_skipped": 0,
        "rows_failed": 0,
        "note": f"Sync framework ready. Implement connector for access_type='{access_type}'.",
    }
