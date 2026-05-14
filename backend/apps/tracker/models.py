from django.db import models


class TrackerTorrentSync(models.Model):
    release = models.OneToOneField(
        "releases.Release",
        on_delete=models.CASCADE,
        related_name="tracker_sync",
    )
    infohash = models.CharField(max_length=40)
    is_whitelisted = models.BooleanField(default=False)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    last_scrape_at = models.DateTimeField(null=True, blank=True)
    last_scrape_seeders = models.PositiveIntegerField(default=0)
    last_scrape_leechers = models.PositiveIntegerField(default=0)
    last_scrape_completed = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "tracker_torrent_sync"
        ordering = ["-last_synced_at", "-id"]

    def __str__(self) -> str:
        return f"{self.release_id}:{self.infohash}"


class TrackerPeerSnapshot(models.Model):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="tracker_peer_snapshots",
    )
    release = models.ForeignKey(
        "releases.Release",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tracker_peer_snapshots",
    )
    infohash = models.CharField(max_length=40, db_index=True)
    peer_id = models.CharField(max_length=40)
    torrent_size_bytes = models.PositiveBigIntegerField(default=0)
    uploaded_bytes = models.PositiveBigIntegerField(default=0)
    downloaded_bytes = models.PositiveBigIntegerField(default=0)
    left_bytes = models.PositiveBigIntegerField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    port = models.PositiveIntegerField(null=True, blank=True)
    last_event = models.CharField(max_length=20, blank=True, default="")
    last_announced_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tracker_peer_snapshots"
        ordering = ["-last_announced_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "infohash", "peer_id"],
                name="uniq_tracker_peer_snapshot_user_infohash_peer",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.infohash}:{self.peer_id}"
