from app.models import (
    audit_log,
    category,
    download_log,
    site_settings,
    torrent,
    torrent_file,
    tracker_torrent_stats_cache,
    tracker_user_stats_cache,
    user,
)


def import_all_models() -> None:
    _ = (
        audit_log,
        category,
        download_log,
        site_settings,
        torrent,
        torrent_file,
        tracker_torrent_stats_cache,
        tracker_user_stats_cache,
        user,
    )
