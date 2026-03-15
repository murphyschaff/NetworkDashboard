from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Service",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("host", models.CharField(max_length=255, help_text="Hostname or IP address")),
                ("port", models.PositiveIntegerField()),
                ("check_type", models.CharField(choices=[("tcp", "TCP Port"), ("http", "HTTP(S)")], default="http", max_length=4)),
                ("http_url", models.CharField(blank=True, help_text="Full URL for HTTP checks. Leave blank to use http://{host}:{port}/", max_length=500)),
                ("enabled", models.BooleanField(default=True)),
                ("display_order", models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")),
                ("tags", models.ManyToManyField(blank=True, to="services.tag")),
            ],
            options={"ordering": ["display_order", "name"]},
        ),
        migrations.CreateModel(
            name="ServiceStatus",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("checked_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("is_up", models.BooleanField()),
                ("response_time_ms", models.FloatField(blank=True, null=True)),
                ("detail", models.CharField(blank=True, max_length=500)),
                ("service", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="statuses", to="services.service")),
            ],
            options={"ordering": ["-checked_at"], "get_latest_by": "checked_at"},
        ),
    ]
