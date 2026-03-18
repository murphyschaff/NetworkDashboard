"""Low-level health check functions. Returns (is_up, response_time_ms, detail)."""
import socket
import time

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def check_tcp(host: str, port: int, timeout: float = 5.0) -> tuple[bool, float | None, str]:
    start = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            elapsed = (time.monotonic() - start) * 1000
            return True, round(elapsed, 2), ""
    except OSError as exc:
        elapsed = (time.monotonic() - start) * 1000
        return False, round(elapsed, 2), str(exc)


def check_http(url: str, timeout: float = 10.0) -> tuple[bool, float | None, str]:
    start = time.monotonic()
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True, verify=True)
        elapsed = (time.monotonic() - start) * 1000
        is_up = response.status_code < 500
        return is_up, round(elapsed, 2), f"HTTP {response.status_code}"
    except requests.exceptions.SSLError as ssl_exc:
        # Certificate problem — retry without verification to check if the service itself is up
        try:
            response = requests.get(url, timeout=timeout, allow_redirects=True, verify=False)
            elapsed = (time.monotonic() - start) * 1000
            is_up = response.status_code < 500
            reason = _ssl_reason(ssl_exc)
            return is_up, round(elapsed, 2), f"SSL: {reason}"
        except Exception:
            elapsed = (time.monotonic() - start) * 1000
            return False, round(elapsed, 2), f"SSL: {_ssl_reason(ssl_exc)}"
    except requests.exceptions.ConnectionError as exc:
        elapsed = (time.monotonic() - start) * 1000
        return False, round(elapsed, 2), f"Connection error: {exc}"
    except requests.exceptions.Timeout:
        elapsed = (time.monotonic() - start) * 1000
        return False, round(elapsed, 2), "Timed out"
    except requests.exceptions.RequestException as exc:
        elapsed = (time.monotonic() - start) * 1000
        return False, round(elapsed, 2), str(exc)


def _ssl_reason(exc: requests.exceptions.SSLError) -> str:
    """Extract a short human-readable reason from an SSLError."""
    msg = str(exc)
    if "CERTIFICATE_VERIFY_FAILED" in msg:
        if "certificate has expired" in msg:
            return "certificate expired"
        if "self-signed" in msg or "self signed" in msg:
            return "self-signed certificate"
        if "hostname mismatch" in msg or "doesn't match" in msg:
            return "hostname mismatch"
        return "certificate verify failed"
    return "TLS error"
