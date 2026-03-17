from django.contrib import admin
from django.utils.html import format_html

from .models import Service, ServiceStatus, Tag
from .tasks import check_service


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class ServiceStatusInline(admin.TabularInline):
    model = ServiceStatus
    fields = ("checked_at", "is_up", "response_time_ms", "detail")
    readonly_fields = ("checked_at", "is_up", "response_time_ms", "detail")
    extra = 0
    max_num = 10
    ordering = ("-checked_at",)
    can_delete = False


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "host", "port", "check_type", "enabled", "current_status", "display_order")
    list_filter = ("check_type", "enabled", "tags")
    search_fields = ("name", "host")
    filter_horizontal = ("tags",)
    inlines = [ServiceStatusInline]
    actions = ["run_check_now"]
    fieldsets = [
        (None, {
            "fields": ("name", "description", "enabled", "display_order", "tags"),
        }),
        ("Check Configuration", {
            "fields": ("host", "port", "check_type", "http_url"),
        }),
        ("LibreNMS", {
            "fields": ("librenms_instance", "librenms_device_id"),
            "classes": ("collapse",),
        }),
    ]

    @admin.display(description="Status")
    def current_status(self, obj):
        latest = obj.latest_status
        if latest is None:
            return "—"
        color = "green" if latest.is_up else "red"
        label = "UP" if latest.is_up else "DOWN"
        return format_html('<span style="color:{}">{}</span>', color, label)

    @admin.action(description="Run health check now")
    def run_check_now(self, request, queryset):
        count = 0
        for service in queryset:
            check_service.delay(service.id)
            count += 1
        self.message_user(request, f"Queued {count} check(s).")


@admin.register(ServiceStatus)
class ServiceStatusAdmin(admin.ModelAdmin):
    list_display = ("service", "checked_at", "is_up", "response_time_ms", "detail")
    list_filter = ("is_up", "service")
    readonly_fields = ("service", "checked_at", "is_up", "response_time_ms", "detail")
    ordering = ("-checked_at",)
