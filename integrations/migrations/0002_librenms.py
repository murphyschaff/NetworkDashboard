from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("integrations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LibreNMSInstance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True, help_text="Display name, e.g. 'Production' or 'Lab'")),
                ("base_url", models.CharField(max_length=255, help_text="e.g. https://librenms.schaff.cc")),
                ("api_token", models.CharField(max_length=255, help_text="LibreNMS API token (X-Auth-Token)")),
            ],
            options={
                "verbose_name": "LibreNMS Instance",
                "verbose_name_plural": "LibreNMS Instances",
            },
        ),
        migrations.CreateModel(
            name="LibreNMSDevice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("instance", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="devices", to="integrations.librenmsinstance")),
                ("device_id", models.PositiveIntegerField()),
                ("hostname", models.CharField(max_length=255)),
                ("display_name", models.CharField(blank=True, max_length=255)),
                ("cpu", models.FloatField(blank=True, null=True)),
                ("memory", models.FloatField(blank=True, null=True)),
                ("storage", models.FloatField(blank=True, null=True)),
                ("metrics_updated_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "LibreNMS Device",
                "verbose_name_plural": "LibreNMS Devices",
                "ordering": ["hostname"],
                "unique_together": {("instance", "device_id")},
            },
        ),
    ]
