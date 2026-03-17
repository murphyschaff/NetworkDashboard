from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="librenms_device_id",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                help_text="LibreNMS device ID to pull CPU/memory/storage from",
            ),
        ),
    ]
