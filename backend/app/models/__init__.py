from app.models import (
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
        category,
        download_log,
        site_settings,
        torrent,
        torrent_file,
        tracker_torrent_stats_cache,
        tracker_user_stats_cache,
        user,
    )
