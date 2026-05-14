from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("releases", "0002_releasewebseedfile"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tracker", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TrackerPeerSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("infohash", models.CharField(db_index=True, max_length=40)),
                ("peer_id", models.CharField(max_length=40)),
                ("torrent_size_bytes", models.PositiveBigIntegerField(default=0)),
                ("uploaded_bytes", models.PositiveBigIntegerField(default=0)),
                ("downloaded_bytes", models.PositiveBigIntegerField(default=0)),
                ("left_bytes", models.PositiveBigIntegerField(default=0)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("port", models.PositiveIntegerField(blank=True, null=True)),
                ("last_event", models.CharField(blank=True, default="", max_length=20)),
                ("last_announced_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "release",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="tracker_peer_snapshots",
                        to="releases.release",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="tracker_peer_snapshots",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "tracker_peer_snapshots",
                "ordering": ["-last_announced_at", "-id"],
            },
        ),
        migrations.AddConstraint(
            model_name="trackerpeersnapshot",
            constraint=models.UniqueConstraint(
                fields=("user", "infohash", "peer_id"),
                name="uniq_tracker_peer_snapshot_user_infohash_peer",
            ),
        ),
    ]
