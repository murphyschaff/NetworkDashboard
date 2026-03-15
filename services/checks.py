"""Low-level health check functions. Returns (is_up, response_time_ms, detail)."""
import socket
import time

import requests


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
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        elapsed = (time.monotonic() - start) * 1000
        is_up = response.status_code < 500
        detail = f"HTTP {response.status_code}"
        return is_up, round(elapsed, 2), detail
    except requests.exceptions.ConnectionError as exc:
        elapsed = (time.monotonic() - start) * 1000
        return False, round(elapsed, 2), f"Connection error: {exc}"
    except requests.exceptions.Timeout:
        elapsed = (time.monotonic() - start) * 1000
        return False, round(elapsed, 2), "Timed out"
    except requests.exceptions.RequestException as exc:
        elapsed = (time.monotonic() - start) * 1000
        return False, round(elapsed, 2), str(exc)
