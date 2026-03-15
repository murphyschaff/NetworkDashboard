"""weather.gov API client. No API key required."""
import logging

import requests

from django.core.cache import cache

logger = logging.getLogger(__name__)

POINTS_URL = "https://api.weather.gov/points/{lat},{lon}"
HEADERS = {"User-Agent": "network-monitor/1.0 (schaff.cc)"}
CACHE_KEY_CURRENT = "weather_current"
CACHE_KEY_FORECAST = "weather_forecast"


def _resolve_grid(settings):
    """Resolve and cache the WFO grid for the configured lat/lon."""
    if settings.wfo and settings.grid_x is not None:
        return settings.wfo, settings.grid_x, settings.grid_y

    url = POINTS_URL.format(lat=round(settings.latitude, 4), lon=round(settings.longitude, 4))
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        props = r.json()["properties"]
        settings.wfo = props["gridId"]
        settings.grid_x = props["gridX"]
        settings.grid_y = props["gridY"]
        settings.save(update_fields=["wfo", "grid_x", "grid_y"])
        return settings.wfo, settings.grid_x, settings.grid_y
    except Exception as exc:
        logger.error("weather.gov points lookup failed: %s", exc)
        return None, None, None


def fetch_current_conditions(settings) -> dict | None:
    """Return current observation from the nearest station."""
    wfo, gx, gy = _resolve_grid(settings)
    if not wfo:
        return None
    try:
        # Get the nearest observation station
        stations_url = f"https://api.weather.gov/gridpoints/{wfo}/{gx},{gy}/stations"
        r = requests.get(stations_url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        stations = r.json()["features"]
        if not stations:
            return None
        station_id = stations[0]["properties"]["stationIdentifier"]

        obs_url = f"https://api.weather.gov/stations/{station_id}/observations/latest"
        r = requests.get(obs_url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        obs = r.json()["properties"]

        temp_c = obs.get("temperature", {}).get("value")
        temp_f = round(temp_c * 9 / 5 + 32, 1) if temp_c is not None else None
        wind_ms = obs.get("windSpeed", {}).get("value")
        wind_mph = round(wind_ms * 2.237, 1) if wind_ms is not None else None

        return {
            "description": obs.get("textDescription", ""),
            "temp_f": temp_f,
            "humidity": obs.get("relativeHumidity", {}).get("value"),
            "wind_mph": wind_mph,
            "wind_direction": obs.get("windDirection", {}).get("value"),
            "icon": obs.get("icon", ""),
            "station": station_id,
        }
    except Exception as exc:
        logger.error("weather.gov current conditions failed: %s", exc)
        return None


def fetch_forecast(settings) -> list | None:
    """Return the next 5 forecast periods."""
    wfo, gx, gy = _resolve_grid(settings)
    if not wfo:
        return None
    try:
        url = f"https://api.weather.gov/gridpoints/{wfo}/{gx},{gy}/forecast"
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        periods = r.json()["properties"]["periods"]
        result = []
        for p in periods[:5]:
            result.append({
                "name": p["name"],
                "temp_f": p["temperature"],
                "temp_trend": p.get("temperatureTrend", ""),
                "wind_speed": p.get("windSpeed", ""),
                "wind_direction": p.get("windDirection", ""),
                "short_forecast": p["shortForecast"],
                "icon": p.get("icon", ""),
                "is_daytime": p["isDaytime"],
            })
        return result
    except Exception as exc:
        logger.error("weather.gov forecast failed: %s", exc)
        return None


def get_cached_current() -> dict | None:
    return cache.get(CACHE_KEY_CURRENT)


def get_cached_forecast() -> list | None:
    return cache.get(CACHE_KEY_FORECAST)


def refresh_cache(settings):
    current = fetch_current_conditions(settings)
    forecast = fetch_forecast(settings)
    if current:
        cache.set(CACHE_KEY_CURRENT, current, timeout=660)
    if forecast:
        cache.set(CACHE_KEY_FORECAST, forecast, timeout=660)
