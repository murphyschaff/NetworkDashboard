from celery import shared_task
from django.utils import timezone

from .checks import check_tcp, check_http
from .models import Service, ServiceStatus


@shared_task
def check_service(service_id: int) -> dict:
    try:
        service = Service.objects.get(pk=service_id, enabled=True)
    except Service.DoesNotExist:
        return {"error": f"Service {service_id} not found"}

    if service.check_type == Service.CHECK_TCP:
        is_up, ms, detail = check_tcp(service.host, service.port)
    else:
        is_up, ms, detail = check_http(service.resolved_http_url)

    ServiceStatus.objects.create(
        service=service,
        checked_at=timezone.now(),
        is_up=is_up,
        response_time_ms=ms,
        detail=detail,
    )

    # Keep only the last 1440 results per service (24h at 1/min)
    old_ids = (
        ServiceStatus.objects.filter(service=service)
        .order_by("-checked_at")
        .values_list("id", flat=True)[1440:]
    )
    if old_ids:
        ServiceStatus.objects.filter(id__in=list(old_ids)).delete()

    return {"service": service.name, "is_up": is_up, "ms": ms}


@shared_task
def check_all_services() -> dict:
    ids = list(Service.objects.filter(enabled=True).values_list("id", flat=True))
    for service_id in ids:
        check_service.delay(service_id)
    return {"queued": len(ids)}
