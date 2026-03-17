"""LibreNMS REST API client."""
import logging

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_KEY = "librenms_devices"
CACHE_TIMEOUT = 360  # 6 minutes


def _headers(instance) -> dict:
    return {"X-Auth-Token": instance.api_token}


def fetch_device(device_id: int, instance) -> dict | None:
    """Fetch CPU, memory, and storage for a single device. Returns None on error."""
    base = instance.base_url.rstrip("/")
    try:
        r = requests.get(
            f"{base}/api/v0/devices/{device_id}",
            headers=_headers(instance),
            timeout=10,
        )
        r.raise_for_status()
        device = r.json().get("devices", [{}])[0]
        cpu = device.get("cpu") or 0.0
        memory = device.get("memperc") or 0.0
    except Exception as exc:
        logger.error("LibreNMS(%s) fetch_device(%s) failed: %s", instance.name, device_id, exc)
        return None

    try:
        r = requests.get(
            f"{base}/api/v0/devices/{device_id}/storage",
            headers=_headers(instance),
            timeout=10,
        )
        r.raise_for_status()
        mounts = r.json().get("storage", [])
        storage = max((m.get("storage_perc", 0) or 0 for m in mounts), default=0.0)
    except Exception as exc:
        logger.error("LibreNMS(%s) fetch_device(%s) storage failed: %s", instance.name, device_id, exc)
        storage = 0.0

    return {"cpu": float(cpu), "memory": float(memory), "storage": float(storage)}


def refresh_cache():
    """Fetch metrics for all services that have a LibreNMS instance + device ID set.

    Cache structure: {instance_pk: {device_id: {cpu, memory, storage}}}
    """
    from services.models import Service

    services = (
        Service.objects
        .filter(librenms_instance__isnull=False, librenms_device_id__isnull=False)
        .select_related("librenms_instance")
    )

    # Group unique (instance, device_id) pairs
    to_fetch: dict[int, tuple] = {}  # instance_pk -> instance object
    pairs: set[tuple[int, int]] = set()
    for svc in services:
        pairs.add((svc.librenms_instance_id, svc.librenms_device_id))
        to_fetch[svc.librenms_instance_id] = svc.librenms_instance

    data: dict[int, dict[int, dict]] = {}
    for instance_pk, device_id in pairs:
        instance = to_fetch[instance_pk]
        result = fetch_device(device_id, instance)
        if result is not None:
            data.setdefault(instance_pk, {})[device_id] = result

    cache.set(CACHE_KEY, data, timeout=CACHE_TIMEOUT)


def get_cached_data() -> dict:
    """Returns {instance_pk: {device_id: {cpu, memory, storage}}}."""
    return cache.get(CACHE_KEY) or {}
