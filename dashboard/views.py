from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from services.models import Service, Tag
from integrations.weather import get_cached_current, get_cached_forecast
from integrations.homeassistant import get_cached_states
from integrations.librenms import get_cached_data as get_librenms_data
from integrations.models import HAEntityConfig


def _service_data():
    services = Service.objects.prefetch_related("tags", "statuses").select_related("librenms_instance").filter(enabled=True)
    librenms = get_librenms_data()
    result = []
    for svc in services:
        latest = svc.statuses.order_by("-checked_at").first()
        result.append({
            "service": svc,
            "latest": latest,
            "tags": list(svc.tags.values_list("name", flat=True)),
            "librenms": (
                librenms.get(svc.librenms_instance_id, {}).get(svc.librenms_device_id)
                if svc.librenms_instance_id and svc.librenms_device_id
                else None
            ),
        })
    return result


def _widget_data():
    ha_configs = HAEntityConfig.objects.filter(show_on_dashboard=True).order_by("display_order")
    ha_states = get_cached_states() or {}
    ha_widgets = []
    for cfg in ha_configs:
        state = ha_states.get(cfg.entity_id, {})
        ha_widgets.append({
            "config": cfg,
            "state": state.get("state", "unavailable"),
            "unit": state.get("unit", ""),
        })
    return {
        "weather_current": get_cached_current(),
        "weather_forecast": get_cached_forecast(),
        "ha_widgets": ha_widgets,
    }


@login_required
def dashboard(request):
    ctx = {
        "services": _service_data(),
        **_widget_data(),
        "refresh_seconds": 60,
    }
    return render(request, "dashboard/dashboard.html", ctx)


@login_required
def dashboard_partial(request):
    """HTMX partial — returns only the service table rows."""
    ctx = {"services": _service_data()}
    return render(request, "dashboard/partials/service_rows.html", ctx)


@login_required
def monitor(request):
    tags = Tag.objects.all()
    selected_tag = request.GET.get("tag", "")
    selected_status = request.GET.get("status", "")
    search = request.GET.get("q", "").strip()

    ctx = {
        "tags": tags,
        "selected_tag": selected_tag,
        "selected_status": selected_status,
        "search": search,
        "refresh_seconds": 60,
    }
    return render(request, "dashboard/monitor.html", ctx)


@login_required
def monitor_partial(request):
    """HTMX partial — filtered service rows for the monitor page."""
    selected_tag = request.GET.get("tag", "")
    selected_status = request.GET.get("status", "")
    search = request.GET.get("q", "").strip()

    services_raw = _service_data()

    if selected_tag:
        services_raw = [s for s in services_raw if selected_tag in s["tags"]]

    if selected_status == "up":
        services_raw = [s for s in services_raw if s["latest"] and s["latest"].is_up]
    elif selected_status == "down":
        services_raw = [s for s in services_raw if not s["latest"] or not s["latest"].is_up]

    if search:
        q = search.lower()
        services_raw = [
            s for s in services_raw
            if q in s["service"].name.lower() or q in s["service"].host.lower()
        ]

    ctx = {"services": services_raw}
    return render(request, "dashboard/partials/service_rows.html", ctx)
