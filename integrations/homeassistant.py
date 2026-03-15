"""Home Assistant REST API client."""
import logging

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_KEY_HA_STATES = "ha_states"


def _headers():
    return {
        "Authorization": f"Bearer {settings.HA_TOKEN}",
        "Content-Type": "application/json",
    }


def fetch_all_entity_ids() -> list[dict] | None:
    """Return all HA states as [{entity_id, friendly_name, state}]. Used in admin to pick entities."""
    try:
        r = requests.get(
            f"{settings.HA_BASE_URL}/api/states",
            headers=_headers(),
            timeout=10,
        )
        r.raise_for_status()
        entities = []
        for s in r.json():
            entities.append({
                "entity_id": s["entity_id"],
                "friendly_name": s.get("attributes", {}).get("friendly_name", s["entity_id"]),
                "state": s["state"],
            })
        return sorted(entities, key=lambda e: e["entity_id"])
    except Exception as exc:
        logger.error("HA fetch_all_entity_ids failed: %s", exc)
        return None


def fetch_selected_states(entity_ids: list[str]) -> dict[str, dict] | None:
    """Return {entity_id: {state, friendly_name, unit, ...}} for the given entity IDs."""
    if not entity_ids:
        return {}
    result = {}
    try:
        r = requests.get(
            f"{settings.HA_BASE_URL}/api/states",
            headers=_headers(),
            timeout=10,
        )
        r.raise_for_status()
        id_set = set(entity_ids)
        for s in r.json():
            if s["entity_id"] in id_set:
                attrs = s.get("attributes", {})
                result[s["entity_id"]] = {
                    "state": s["state"],
                    "friendly_name": attrs.get("friendly_name", s["entity_id"]),
                    "unit": attrs.get("unit_of_measurement", ""),
                    "icon": attrs.get("icon", ""),
                }
        return result
    except Exception as exc:
        logger.error("HA fetch_selected_states failed: %s", exc)
        return None


def get_cached_states() -> dict | None:
    return cache.get(CACHE_KEY_HA_STATES)


def refresh_cache():
    from .models import HAEntityConfig
    configs = list(HAEntityConfig.objects.filter(show_on_dashboard=True).values_list("entity_id", flat=True))
    if not configs:
        cache.set(CACHE_KEY_HA_STATES, {}, timeout=120)
        return
    states = fetch_selected_states(configs)
    if states is not None:
        cache.set(CACHE_KEY_HA_STATES, states, timeout=120)
