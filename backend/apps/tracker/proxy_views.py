from django.http import HttpResponse
from django.views import View

from apps.tracker.proxy import TrackerProxyService


def _extract_remote_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class TrackerAnnounceProxyView(View):
    def get(self, request, auth_key: str):
        result = TrackerProxyService.proxy_announce(
            auth_key=auth_key,
            query_string=request.META.get("QUERY_STRING", ""),
            remote_ip=_extract_remote_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return HttpResponse(result.body, status=result.status_code, content_type=result.content_type)


class TrackerScrapeProxyView(View):
    def get(self, request, auth_key: str):
        result = TrackerProxyService.proxy_scrape(
            auth_key=auth_key,
            query_string=request.META.get("QUERY_STRING", ""),
            remote_ip=_extract_remote_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return HttpResponse(result.body, status=result.status_code, content_type=result.content_type)
