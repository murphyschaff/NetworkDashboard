from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SiteSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("latitude", models.FloatField(default=43.0731, help_text="Latitude for weather.gov lookup")),
                ("longitude", models.FloatField(default=-89.4012, help_text="Longitude for weather.gov lookup")),
                ("wfo", models.CharField(blank=True, help_text="Weather Forecast Office (e.g. MKX)", max_length=10)),
                ("grid_x", models.IntegerField(blank=True, null=True)),
                ("grid_y", models.IntegerField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Site Settings",
            },
        ),
        migrations.CreateModel(
            name="HAEntityConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("entity_id", models.CharField(max_length=255, unique=True)),
                ("friendly_name", models.CharField(blank=True, max_length=255)),
                ("show_on_dashboard", models.BooleanField(default=True)),
                ("display_order", models.PositiveIntegerField(default=0)),
            ],
            options={
                "verbose_name": "Home Assistant Entity",
                "verbose_name_plural": "Home Assistant Entities",
                "ordering": ["display_order", "friendly_name"],
            },
        ),
    ]
