from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("announcements", "0002_sitesetting_branding_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesetting",
            name="allow_public_registration",
            field=models.BooleanField(default=False),
        ),
    ]
