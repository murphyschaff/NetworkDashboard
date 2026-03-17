from celery import shared_task


@shared_task
def refresh_weather():
    from .models import SiteSettings
    from .weather import refresh_cache
    settings = SiteSettings.get_solo()
    refresh_cache(settings)


@shared_task
def refresh_ha_states():
    from .homeassistant import refresh_cache
    refresh_cache()


@shared_task
def refresh_librenms_data():
    from . import librenms
    librenms.refresh_all_metrics()
