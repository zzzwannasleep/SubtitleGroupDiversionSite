from django.db import migrations, models

from apps.common.utils import generate_passkey


def populate_api_tokens(apps, schema_editor):
    User = apps.get_model("users", "User")
    for user in User.objects.filter(api_token__isnull=True).iterator():
        user.api_token = generate_passkey()
        user.save(update_fields=["api_token"])


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_user_theme_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="api_token",
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.RunPython(populate_api_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="api_token",
            field=models.CharField(default=generate_passkey, max_length=32, unique=True),
        ),
    ]
