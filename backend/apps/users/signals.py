from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.tracker_sync.services import TrackerSyncService
from apps.users.models import User


TRACKER_SYNC_RELEVANT_FIELDS = {"passkey", "status"}


@receiver(post_save, sender=User)
def sync_user_to_xbt_after_save(sender, instance: User, created: bool, raw: bool, update_fields=None, **kwargs):
    if raw:
        return

    if created:
        should_sync = True
    elif update_fields is None:
        # Direct model saves such as createsuperuser or Django admin edits may not
        # provide update_fields. Prefer syncing rather than leaving XBT stale.
        should_sync = True
    else:
        should_sync = bool(TRACKER_SYNC_RELEVANT_FIELDS.intersection(update_fields))

    if not should_sync:
        return

    transaction.on_commit(lambda: TrackerSyncService.sync_user_by_id(instance.id))
