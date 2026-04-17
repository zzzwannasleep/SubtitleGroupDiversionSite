from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("announcements", "0003_sitesetting_allow_public_registration"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesetting",
            name="login_page_css",
            field=models.TextField(blank=True, default=""),
        ),
    ]
