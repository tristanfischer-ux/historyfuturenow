"""HFN Promote — GA4 Analytics (Google Analytics Data API)"""
import time, threading
from pathlib import Path
from config import GA4_PROPERTY_ID

_cache = {}
_cache_ts = 0
_CACHE_TTL = 900  # 15 minutes
_cache_lock = threading.Lock()

SERVICE_ACCOUNT_PATH = Path(__file__).resolve().parent / "ga4-service-account.json"


def _build_client():
    """Create GA4 BetaAnalyticsDataClient from service account JSON."""
    if not SERVICE_ACCOUNT_PATH.exists() or not GA4_PROPERTY_ID:
        return None
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        return BetaAnalyticsDataClient.from_service_account_json(str(SERVICE_ACCOUNT_PATH))
    except Exception:
        return None


def _run_report(client, property_id, days):
    """Run a GA4 report for page views/users filtered to /articles/* paths."""
    from google.analytics.data_v1beta.types import (
        RunReportRequest, DateRange, Dimension, Metric, FilterExpression, Filter,
    )
    req = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
        dimensions=[Dimension(name="pagePath")],
        metrics=[Metric(name="screenPageViews"), Metric(name="totalUsers")],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="pagePath",
                string_filter=Filter.StringFilter(
                    match_type=Filter.StringFilter.MatchType.BEGINS_WITH,
                    value="/articles/",
                ),
            )
        ),
        limit=500,
    )
    return client.run_report(req)


def fetch_article_analytics(property_id=None):
    """Fetch 7d + 30d page views/users for all /articles/* paths.

    Returns: {"/articles/slug": {"views_7d", "users_7d", "views_30d", "users_30d"}}
    Graceful: returns {} if no service account or API errors.
    """
    global _cache, _cache_ts
    with _cache_lock:
        if _cache and (time.time() - _cache_ts) < _CACHE_TTL:
            return _cache

    pid = property_id or GA4_PROPERTY_ID
    if not pid:
        return {}

    client = _build_client()
    if not client:
        return {}

    try:
        data = {}
        for days, suffix in [(7, "7d"), (30, "30d")]:
            resp = _run_report(client, pid, days)
            for row in resp.rows:
                path = row.dimension_values[0].value.rstrip("/")
                if path not in data:
                    data[path] = {"views_7d": 0, "users_7d": 0, "views_30d": 0, "users_30d": 0}
                data[path][f"views_{suffix}"] = int(row.metric_values[0].value)
                data[path][f"users_{suffix}"] = int(row.metric_values[1].value)

        with _cache_lock:
            _cache = data
            _cache_ts = time.time()
        return data
    except Exception:
        return {}


def get_analytics_for_slug(slug, data):
    """Lookup analytics for a slug, trying both /articles/slug and /articles/slug/."""
    if not data:
        return None
    path = f"/articles/{slug}"
    return data.get(path) or data.get(path + "/")


def fetch_post_performance():
    """Fetch GA4 UTM campaign data for post performance tracking.
    Looks for campaigns named 'post_<id>' and maps back to post IDs."""
    import db

    pid = GA4_PROPERTY_ID
    if not pid:
        return 0

    client = _build_client()
    if not client:
        return 0

    try:
        from google.analytics.data_v1beta.types import (
            RunReportRequest, DateRange, Dimension, Metric, FilterExpression, Filter,
        )
        updated = 0
        for days, click_col, user_col in [(7, "clicks_7d", "users_7d"),
                                           (30, "clicks_30d", "users_30d")]:
            req = RunReportRequest(
                property=f"properties/{pid}",
                date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
                dimensions=[Dimension(name="sessionCampaignName")],
                metrics=[Metric(name="sessions"), Metric(name="totalUsers")],
                dimension_filter=FilterExpression(
                    filter=Filter(
                        field_name="sessionCampaignName",
                        string_filter=Filter.StringFilter(
                            match_type=Filter.StringFilter.MatchType.BEGINS_WITH,
                            value="post_",
                        ),
                    )
                ),
                limit=500,
            )
            resp = client.run_report(req)
            for row in resp.rows:
                campaign = row.dimension_values[0].value
                # Extract post_id from "post_123"
                try:
                    post_id = int(campaign.split("_", 1)[1])
                except (ValueError, IndexError):
                    continue
                clicks = int(row.metric_values[0].value)
                users = int(row.metric_values[1].value)
                # Upsert — we call twice (7d then 30d), so use kwargs
                existing = db.get_post_performance(post_id)
                if existing:
                    kwargs = dict(existing)
                    kwargs.pop("id", None)
                    kwargs.pop("post_id", None)
                    kwargs.pop("last_fetched", None)
                else:
                    kwargs = {"clicks_7d": 0, "clicks_30d": 0, "users_7d": 0, "users_30d": 0}
                kwargs[click_col] = clicks
                kwargs[user_col] = users
                db.upsert_post_performance(post_id, **kwargs)
                updated += 1
        return updated
    except Exception as ex:
        print(f"  [!] Post performance fetch error: {ex}")
        return 0
