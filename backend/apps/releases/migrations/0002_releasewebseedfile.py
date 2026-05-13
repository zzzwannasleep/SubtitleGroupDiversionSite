from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("releases", "0002_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReleaseWebseedFile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("relative_path", models.CharField(max_length=700)),
                ("storage_file", models.FileField(upload_to="release-webseeds/")),
                ("size_bytes", models.BigIntegerField(default=0)),
                (
                    "release",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="webseed_files",
                        to="releases.release",
                    ),
                ),
            ],
            options={
                "db_table": "release_webseed_files",
                "ordering": ["id"],
            },
        ),
        migrations.AddConstraint(
            model_name="releasewebseedfile",
            constraint=models.UniqueConstraint(
                fields=("release", "relative_path"),
                name="uniq_release_webseed_relative_path",
            ),
        ),
    ]
