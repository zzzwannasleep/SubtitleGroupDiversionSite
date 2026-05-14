from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("announcements", "0004_sitesetting_login_page_css"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesetting",
            name="site_custom_css",
            field=models.TextField(blank=True, default=""),
        ),
    ]
