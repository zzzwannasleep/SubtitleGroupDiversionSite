from django.core.management.base import BaseCommand, CommandError

from apps.releases.services import ReleaseService
from apps.releases.models import Release
from apps.tracker.services import TrackerService, TrackerSyncService
from apps.users.models import User


class Command(BaseCommand):
    help = "Synchronize existing users and releases to Torrust tracker state."

    def add_arguments(self, parser):
        parser.add_argument("--users", action="store_true", help="Provision tracker keys for active users.")
        parser.add_argument("--releases", action="store_true", help="Synchronize published releases to tracker whitelist.")
        parser.add_argument("--scrape", action="store_true", help="Scrape published releases and write tracker stats back.")

    def handle(self, *args, **options):
        if not TrackerService.is_enabled():
            raise CommandError("Tracker integration is not enabled.")

        sync_users = options["users"]
        sync_releases = options["releases"]
        sync_scrape = options["scrape"]
        if not sync_users and not sync_releases and not sync_scrape:
            sync_users = True
            sync_releases = True
            sync_scrape = True

        if sync_users:
            self.stdout.write("Synchronizing active user tracker keys...")
            for user in User.objects.filter(status="active").order_by("id"):
                key = TrackerService.ensure_user_key(user)
                self.stdout.write(f"  user={user.username} key={key[:8]}...")

        if sync_releases:
            self.stdout.write("Synchronizing release whitelist state...")
            queryset = Release.objects.select_related("created_by").order_by("id")
            for release in queryset:
                release = ReleaseService.normalize_existing_release_torrent(release)
                sync = TrackerSyncService.sync_release_now(release=release)
                self.stdout.write(
                    f"  release={release.id} status={release.status} whitelisted={sync.is_whitelisted} error={bool(sync.last_error)}"
                )

        if sync_scrape:
            self.stdout.write("Scraping published release stats...")
            queryset = Release.objects.select_related("created_by").filter(status="published").order_by("id")
            for release in queryset:
                sync = TrackerSyncService.sync_release_scrape_now(release=release)
                self.stdout.write(
                    "  "
                    f"release={release.id} seeders={sync.last_scrape_seeders} "
                    f"leechers={sync.last_scrape_leechers} completed={sync.last_scrape_completed} "
                    f"error={bool(sync.last_error)}"
                )
