from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0007_alter_user_managers"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="downloaded_bytes",
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="user",
            name="seeding_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="user",
            name="seeding_size_bytes",
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="user",
            name="uploaded_bytes",
            field=models.PositiveBigIntegerField(default=0),
        ),
    ]
