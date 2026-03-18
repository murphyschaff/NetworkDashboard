from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("integrations", "0002_librenms"),
    ]

    operations = [
        migrations.AddField(
            model_name="librenmsinstance",
            name="db_host",
            field=models.CharField(blank=True, help_text="LibreNMS MySQL host (leave blank to skip direct DB metrics)", max_length=255),
        ),
        migrations.AddField(
            model_name="librenmsinstance",
            name="db_port",
            field=models.PositiveIntegerField(default=3306),
        ),
        migrations.AddField(
            model_name="librenmsinstance",
            name="db_name",
            field=models.CharField(default="librenms", max_length=100),
        ),
        migrations.AddField(
            model_name="librenmsinstance",
            name="db_user",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="librenmsinstance",
            name="db_password",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
