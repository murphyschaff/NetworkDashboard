"""LibreNMS REST API client."""
import logging

import requests
import urllib3
from django.utils import timezone

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


def _headers(instance) -> dict:
    return {"X-Auth-Token": instance.api_token}


def fetch_device_metrics(device_id: int, instance) -> dict | None:
    """Fetch CPU, memory, and storage for a single device. Returns None on error."""
    base = instance.base_url.rstrip("/")
    try:
        r = requests.get(
            f"{base}/api/v0/devices/{device_id}",
            headers=_headers(instance),
            timeout=10,
            verify=False,
        )
        r.raise_for_status()
        device = r.json().get("devices", [{}])[0]
        cpu = device.get("cpu") or 0.0
        memory = device.get("memperc") or 0.0
    except Exception as exc:
        logger.error("LibreNMS(%s) fetch_device_metrics(%s) failed: %s", instance.name, device_id, exc)
        return None

    try:
        r = requests.get(
            f"{base}/api/v0/devices/{device_id}/storage",
            headers=_headers(instance),
            timeout=10,
            verify=False,
        )
        r.raise_for_status()
        mounts = r.json().get("storage", [])
        storage = max((m.get("storage_perc", 0) or 0 for m in mounts), default=0.0)
    except Exception as exc:
        logger.error("LibreNMS(%s) fetch_device_metrics(%s) storage failed: %s", instance.name, device_id, exc)
        storage = 0.0

    return {"cpu": float(cpu), "memory": float(memory), "storage": float(storage)}


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
    except Exception as exc:
        logger.error("LibreNMS(%s) import_devices failed: %s", instance.name, exc)
        return 0

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
