from django.db import models
from django.utils import timezone


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Service(models.Model):
    CHECK_TCP = "tcp"
    CHECK_HTTP = "http"
    CHECK_CHOICES = [
        (CHECK_TCP, "TCP Port"),
        (CHECK_HTTP, "HTTP(S)"),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    host = models.CharField(max_length=255, help_text="Hostname or IP address")
    port = models.PositiveIntegerField()
    check_type = models.CharField(max_length=4, choices=CHECK_CHOICES, default=CHECK_HTTP)
    http_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="Full URL for HTTP checks (e.g. https://app.schaff.cc/health). Leave blank to use http://{host}:{port}/",
    )
    tags = models.ManyToManyField(Tag, blank=True)
    enabled = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")
    librenms_device_id = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="LibreNMS device ID to pull CPU/memory/storage from"
    )
    librenms_instance = models.ForeignKey(
        "integrations.LibreNMSInstance",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="Which LibreNMS instance this device belongs to"
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["display_order", "name"]

    @property
    def resolved_http_url(self):
        if self.http_url:
            return self.http_url
        return f"http://{self.host}:{self.port}/"

    @property
    def latest_status(self):
        return self.statuses.order_by("-checked_at").first()


class ServiceStatus(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="statuses")
    checked_at = models.DateTimeField(default=timezone.now)
    is_up = models.BooleanField()
    response_time_ms = models.FloatField(null=True, blank=True)
    detail = models.CharField(max_length=500, blank=True)

    def __str__(self):
        status = "UP" if self.is_up else "DOWN"
        return f"{self.service.name} — {status} at {self.checked_at:%Y-%m-%d %H:%M:%S}"

    class Meta:
        ordering = ["-checked_at"]
        get_latest_by = "checked_at"
