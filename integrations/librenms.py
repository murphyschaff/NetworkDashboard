"""LibreNMS REST API client."""
import logging

import requests
import urllib3
from django.utils import timezone

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


def _headers(instance) -> dict:
    return {"X-Auth-Token": instance.api_token}


def test_connection(instance) -> tuple[bool, str]:
    """Hit /api/v0/system to verify the URL and token are valid."""
    base = instance.base_url.rstrip("/")
    try:
        r = requests.get(
            f"{base}/api/v0/system",
            headers=_headers(instance),
            timeout=10,
            verify=False,
        )
        r.raise_for_status()
        version = r.json().get("system", {}).get("local_ver", "unknown")
        return True, f"Connected — LibreNMS {version}"
    except requests.exceptions.ConnectionError as exc:
        return False, f"Connection error: {exc}"
    except requests.exceptions.Timeout:
        return False, "Request timed out"
    except requests.exceptions.HTTPError as exc:
        return False, f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"
    except Exception as exc:
        return False, str(exc)


def fetch_device_metrics(device_id: int, instance) -> dict | None:
    """Fetch CPU, memory, and storage for a single device.

    CPU and memory are queried directly from the LibreNMS MySQL database (REST API
    does not expose this data for UCD-SNMP monitored devices). Storage falls back to
    the REST API if no DB connection is configured.
    """
    cpu, memory, storage = None, None, None

    if instance.db_host:
        cpu, memory, storage = _fetch_metrics_from_db(device_id, instance)

    if storage is None:
        storage = _fetch_storage_from_api(device_id, instance)

    if cpu is None and memory is None and storage is None:
        return None

    return {
        "cpu": cpu,
        "memory": memory,
        "storage": storage,
    }


def _fetch_metrics_from_db(device_id: int, instance) -> tuple:
    """Query processors, mempools, and storage tables directly. Returns (cpu, memory, storage)."""
    import pymysql

    try:
        conn = pymysql.connect(
            host=instance.db_host,
            port=instance.db_port,
            database=instance.db_name,
            user=instance.db_user,
            password=instance.db_password,
            connect_timeout=5,
        )
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT AVG(processor_usage) FROM processors WHERE device_id = %s", (device_id,))
                row = cur.fetchone()
                cpu = float(row[0]) if row and row[0] is not None else None

                cur.execute("SELECT AVG(mempool_perc) FROM mempools WHERE device_id = %s", (device_id,))
                row = cur.fetchone()
                memory = float(row[0]) if row and row[0] is not None else None

                cur.execute("SELECT MAX(storage_perc) FROM storage WHERE device_id = %s", (device_id,))
                row = cur.fetchone()
                storage = float(row[0]) if row and row[0] is not None else None

        return cpu, memory, storage
    except Exception as exc:
        logger.error("LibreNMS(%s) DB metrics(%s) failed: %s", instance.name, device_id, exc)
        return None, None, None


def _fetch_storage_from_api(device_id: int, instance) -> float | None:
    """Fallback: fetch storage via REST API."""
    base = instance.base_url.rstrip("/")
    try:
        r = requests.get(
            f"{base}/api/v0/devices/{device_id}/storage",
            headers=_headers(instance),
            timeout=10,
            verify=False,
        )
        r.raise_for_status()
        mounts = r.json().get("storage", [])
        return float(max((m.get("storage_perc", 0) or 0 for m in mounts), default=0.0))
    except Exception as exc:
        logger.error("LibreNMS(%s) API storage(%s) failed: %s", instance.name, device_id, exc)
        return None


def import_devices(instance) -> int:
    """Fetch all devices from LibreNMS and upsert them into LibreNMSDevice.

    Returns the count of devices created or updated.
    """
    from .models import LibreNMSDevice

    base = instance.base_url.rstrip("/")
    try:
        r = requests.get(
            f"{base}/api/v0/devices",
            headers=_headers(instance),
            timeout=15,
            verify=False,
        )
        r.raise_for_status()
        devices = r.json().get("devices", [])
    except requests.exceptions.HTTPError as exc:
        msg = f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"
        logger.error("LibreNMS(%s) import_devices failed: %s", instance.name, msg)
        raise RuntimeError(msg) from exc
    except Exception as exc:
        logger.error("LibreNMS(%s) import_devices failed: %s", instance.name, exc)
        raise RuntimeError(str(exc)) from exc

    count = 0
    for d in devices:
        device_id = d.get("device_id")
        if device_id is None:
            continue
        LibreNMSDevice.objects.update_or_create(
            instance=instance,
            device_id=device_id,
            defaults={"hostname": d.get("hostname", "")},
            create_defaults={"display_name": d.get("display") or d.get("sysName") or d.get("hostname", "")},
        )
        count += 1
    return count


def refresh_all_metrics():
    """Fetch and save metrics for every LibreNMSDevice."""
    from .models import LibreNMSDevice

    devices = LibreNMSDevice.objects.select_related("instance").all()
    for device in devices:
        result = fetch_device_metrics(device.device_id, device.instance)
        if result is not None:
            device.cpu = result["cpu"]
            device.memory = result["memory"]
            device.storage = result["storage"]
            device.metrics_updated_at = timezone.now()
            device.save(update_fields=["cpu", "memory", "storage", "metrics_updated_at"])
