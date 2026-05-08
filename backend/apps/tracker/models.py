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

