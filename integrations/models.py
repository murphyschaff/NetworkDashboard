from django.db import models
from solo.models import SingletonModel


class SiteSettings(SingletonModel):
    latitude = models.FloatField(default=43.0731, help_text="Latitude for weather.gov lookup")
    longitude = models.FloatField(default=-89.4012, help_text="Longitude for weather.gov lookup")
    # Cached after first successful weather.gov points lookup
    wfo = models.CharField(max_length=10, blank=True, help_text="Weather Forecast Office (e.g. MKX)")
    grid_x = models.IntegerField(null=True, blank=True)
    grid_y = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return "Site Settings"

    def clear_weather_grid(self):
        """Call after changing lat/lon so grid is re-resolved on next check."""
        self.wfo = ""
        self.grid_x = None
        self.grid_y = None
        self.save(update_fields=["wfo", "grid_x", "grid_y"])

    class Meta:
        verbose_name = "Site Settings"


class HAEntityConfig(models.Model):
    entity_id = models.CharField(max_length=255, unique=True)
    friendly_name = models.CharField(max_length=255, blank=True)
    show_on_dashboard = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.friendly_name or self.entity_id

    class Meta:
        ordering = ["display_order", "friendly_name"]
        verbose_name = "Home Assistant Entity"
        verbose_name_plural = "Home Assistant Entities"
