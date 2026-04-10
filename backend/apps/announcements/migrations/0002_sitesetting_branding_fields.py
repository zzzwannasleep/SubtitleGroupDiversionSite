from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("announcements", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesetting",
            name="login_background_api_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="sitesetting",
            name="login_background_css",
            field=models.TextField(
                blank=True,
                default=(
                    "radial-gradient(circle at top left, rgba(96, 165, 250, 0.38), transparent 34%), "
                    "radial-gradient(circle at 85% 15%, rgba(244, 114, 182, 0.28), transparent 30%), "
                    "linear-gradient(135deg, #020617 0%, #0f172a 46%, #111827 100%)"
                ),
            ),
        ),
        migrations.AddField(
            model_name="sitesetting",
            name="login_background_file",
            field=models.FileField(blank=True, upload_to="site/login-backgrounds/"),
        ),
        migrations.AddField(
            model_name="sitesetting",
            name="login_background_type",
            field=models.CharField(
                choices=[("api", "API"), ("file", "文件"), ("css", "CSS")],
                default="css",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="sitesetting",
            name="site_icon_file",
            field=models.FileField(blank=True, upload_to="site/branding/"),
        ),
        migrations.AddField(
            model_name="sitesetting",
            name="site_icon_url",
            field=models.URLField(blank=True),
        ),
    ]
