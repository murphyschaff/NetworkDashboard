from django.db import migrations, models


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
    ]
