from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path
from django.utils.html import format_html
from solo.admin import SingletonModelAdmin

from .models import HAEntityConfig, LibreNMSDevice, LibreNMSInstance, SiteSettings
from . import homeassistant


@admin.register(LibreNMSInstance)
class LibreNMSInstanceAdmin(admin.ModelAdmin):
    list_display = ("name", "base_url")
    fields = ("name", "base_url", "api_token")
    actions = ["import_devices"]

    @admin.action(description="Import / sync devices from LibreNMS")
    def import_devices(self, request, queryset):
        from . import librenms
        total = 0
        for instance in queryset:
            total += librenms.import_devices(instance)
        self.message_user(request, f"Imported/updated {total} device(s).")


@admin.register(LibreNMSDevice)
class LibreNMSDeviceAdmin(admin.ModelAdmin):
    list_display = ("hostname", "display_name", "instance", "cpu", "memory", "storage", "metrics_updated_at")
    list_filter = ("instance",)
    search_fields = ("hostname", "display_name")
    readonly_fields = ("instance", "device_id", "hostname", "display_name", "cpu", "memory", "storage", "metrics_updated_at")


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonModelAdmin):
    fieldsets = (
        ("Location (for weather.gov)", {
            "fields": ("latitude", "longitude"),
            "description": (
                "Updating latitude/longitude will clear the cached grid point. "
                "The new grid will be resolved automatically on the next weather refresh."
            ),
        }),
        ("Resolved Weather Grid (read-only)", {
            "fields": ("wfo", "grid_x", "grid_y"),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("wfo", "grid_x", "grid_y")

    def save_model(self, request, obj, form, change):
        if change and ("latitude" in form.changed_data or "longitude" in form.changed_data):
            obj.wfo = ""
            obj.grid_x = None
            obj.grid_y = None
        super().save_model(request, obj, form, change)


@admin.register(HAEntityConfig)
class HAEntityConfigAdmin(admin.ModelAdmin):
    list_display = ("friendly_name", "entity_id", "current_state", "show_on_dashboard", "display_order")
    list_editable = ("show_on_dashboard", "display_order")
    search_fields = ("entity_id", "friendly_name")
    ordering = ("display_order", "friendly_name")
    actions = ["import_from_ha"]

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("import-from-ha/", self.admin_site.admin_view(self.import_from_ha_view), name="integrations_haentityconfig_import"),
        ]
        return custom + urls

    def import_from_ha_view(self, request):
        self._run_import(request)
        return redirect("../")

    @admin.display(description="Current State")
    def current_state(self, obj):
        states = homeassistant.get_cached_states() or {}
        entry = states.get(obj.entity_id)
        if entry:
            return f"{entry['state']} {entry['unit']}".strip()
        return "—"

    @admin.action(description="Import / sync entities from Home Assistant")
    def import_from_ha(self, request, queryset):
        self._run_import(request)

    def _run_import(self, request):
        all_entities = homeassistant.fetch_all_entity_ids()
        if all_entities is None:
            self.message_user(request, "Could not reach Home Assistant.", level="error")
            return
        created = 0
        for e in all_entities:
            _, was_created = HAEntityConfig.objects.get_or_create(
                entity_id=e["entity_id"],
                defaults={
                    "friendly_name": e["friendly_name"],
                    "show_on_dashboard": False,
                },
            )
            if was_created:
                created += 1
        self.message_user(request, f"Imported {created} new entit{'y' if created == 1 else 'ies'} from Home Assistant.")
