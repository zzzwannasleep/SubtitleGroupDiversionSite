from django.core.management.base import BaseCommand, CommandError

from apps.tracker.services import TrackerAdminService, TrackerService


class Command(BaseCommand):
    help = "Synchronize existing users and releases to Torrust tracker state."

    def add_arguments(self, parser):
        parser.add_argument("--users", action="store_true", help="Provision tracker keys for active users.")
        parser.add_argument("--releases", action="store_true", help="Synchronize published releases to tracker whitelist.")
        parser.add_argument("--scrape", action="store_true", help="Scrape published releases and write tracker stats back.")
        parser.add_argument(
            "--fail-on-error",
            action="store_true",
            help="Return a non-zero exit code if any user, release, or scrape synchronization fails.",
        )

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
        summary = TrackerAdminService.sync(
            sync_users=sync_users,
            sync_releases=sync_releases,
            sync_scrape=sync_scrape,
        )

        if sync_users:
            self.stdout.write(
                f"Synchronizing active user tracker keys: processed={summary['usersProcessed']} failed={summary['usersFailed']}"
            )
        if sync_releases:
            self.stdout.write(
                "Synchronizing release whitelist state: "
                f"processed={summary['releasesProcessed']} failed={summary['releasesFailed']}"
            )
        if sync_scrape:
            self.stdout.write(
                f"Scraping published release stats: processed={summary['scrapesProcessed']} failed={summary['scrapesFailed']}"
            )

        errors = summary["errors"]
        if errors:
            self.stdout.write(self.style.WARNING("Tracker synchronization finished with warnings:"))
            for item in errors:
                self.stdout.write(f"  - {item}")
            if options["fail_on_error"]:
                raise CommandError("Tracker synchronization finished with warnings.")
            return

        self.stdout.write(self.style.SUCCESS("Tracker synchronization completed successfully."))
