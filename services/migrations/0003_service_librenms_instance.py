import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("integrations", "0002_librenmsinstance"),
        ("services", "0002_service_librenms_device_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="librenms_instance",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="integrations.librenmsinstance",
                help_text="Which LibreNMS instance this device belongs to",
            ),
        ),
    ]
