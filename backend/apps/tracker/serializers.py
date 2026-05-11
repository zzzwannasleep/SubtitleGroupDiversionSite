from rest_framework import serializers


class TrackerApiStatsSerializer(serializers.Serializer):
    torrents = serializers.IntegerField()
    seeders = serializers.IntegerField()
    leechers = serializers.IntegerField()
    completed = serializers.IntegerField()
    announcesHandled = serializers.IntegerField()
    scrapesHandled = serializers.IntegerField()


class SelfTrackerProfileSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    authMode = serializers.CharField()
    announceUrl = serializers.CharField(allow_blank=True)
    scrapeUrl = serializers.CharField(allow_blank=True)
    passkey = serializers.CharField(allow_blank=True)
    keyValidUntil = serializers.DateTimeField(allow_null=True)
    requireAuthDownloads = serializers.BooleanField()
    forcePrivateTorrents = serializers.BooleanField()


class AdminTrackerOverviewSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    trackerReachable = serializers.BooleanField()
    trackerMessage = serializers.CharField(allow_blank=True)
    authMode = serializers.CharField()
    announceUrl = serializers.CharField(allow_blank=True)
    scrapeUrl = serializers.CharField(allow_blank=True)
    requireAuthDownloads = serializers.BooleanField()
    forcePrivateTorrents = serializers.BooleanField()
    userCount = serializers.IntegerField()
    activeUserCount = serializers.IntegerField()
    userKeysProvisioned = serializers.IntegerField()
    releaseSyncCount = serializers.IntegerField()
    publishedReleaseCount = serializers.IntegerField()
    whitelistedReleaseCount = serializers.IntegerField()
    syncErrorCount = serializers.IntegerField()
    latestSyncAt = serializers.DateTimeField(allow_null=True)
    latestScrapeAt = serializers.DateTimeField(allow_null=True)
    trackerStats = TrackerApiStatsSerializer(allow_null=True)


class AdminTrackerSyncRequestSerializer(serializers.Serializer):
    syncUsers = serializers.BooleanField(required=False, default=False)
    syncReleases = serializers.BooleanField(required=False, default=False)
    syncScrape = serializers.BooleanField(required=False, default=False)


class AdminTrackerSyncResultSerializer(serializers.Serializer):
    usersProcessed = serializers.IntegerField()
    usersFailed = serializers.IntegerField()
    releasesProcessed = serializers.IntegerField()
    releasesFailed = serializers.IntegerField()
    scrapesProcessed = serializers.IntegerField()
    scrapesFailed = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.CharField())
