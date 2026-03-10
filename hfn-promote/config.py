"""HFN Promote — Configuration"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MATCH_MODEL = os.getenv("MATCH_MODEL", "claude-sonnet-4-20250514")
GEN_MODEL = os.getenv("GEN_MODEL", "claude-opus-4-6")

# HFN source paths
HFN_SOURCE_DIR = Path(os.path.expanduser(os.getenv(
    "HFN_SOURCE_DIR",
    "~/Developer/History Future Now 260215/hfn-build-system"
)))
HFN_SITE_OUTPUT = HFN_SOURCE_DIR.parent / "hfn-site-output"
HFN_ARTICLE_IMAGES = HFN_SITE_OUTPUT / "images" / "articles"
HFN_CONTENT_DIR = HFN_SOURCE_DIR / "essays"
HFN_AUDIO_DIR = HFN_SITE_OUTPUT / "audio"
HFN_BASE_URL = "https://www.historyfuturenow.com"

# Database
DB_PATH = BASE_DIR / "hfn.db"

# Sessions
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

# Limits
MAX_X_PER_DAY = int(os.getenv("MAX_X_PER_DAY", "6"))
MAX_LI_PER_DAY = int(os.getenv("MAX_LI_PER_DAY", "6"))
MAX_POSTS_PER_DAY = int(os.getenv("MAX_POSTS_PER_DAY", "12"))
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "30"))
MIN_RELEVANCE = float(os.getenv("MIN_RELEVANCE", "0.5"))

# RSS Feeds — fast-rotating sources first, then quality outlets
RSS_FEEDS = [
    # Google Trends — what people are actually searching for right now
    {"name": "Google Trends UK",  "url": "https://trends.google.com/trending/rss?geo=GB"},
    {"name": "Google Trends US",  "url": "https://trends.google.com/trending/rss?geo=US"},
    {"name": "Google Trends World","url": "https://trends.google.com/trending/rss?geo="},
    # Google News — aggregates fastest, updates every few minutes
    {"name": "Google News UK",      "url": "https://news.google.com/rss?hl=en-GB&gl=GB&ceid=GB:en"},
    {"name": "Google News Business","url": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-GB&gl=GB&ceid=GB:en"},
    {"name": "Google News Tech",    "url": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-GB&gl=GB&ceid=GB:en"},
    {"name": "Google News Science", "url": "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=en-GB&gl=GB&ceid=GB:en"},
    {"name": "Google News World",   "url": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-GB&gl=GB&ceid=GB:en"},
    # Core outlets
    {"name": "BBC World",        "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"name": "BBC Business",     "url": "http://feeds.bbci.co.uk/news/business/rss.xml"},
    {"name": "BBC Tech",         "url": "http://feeds.bbci.co.uk/news/technology/rss.xml"},
    {"name": "BBC Science",      "url": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml"},
    {"name": "Reuters World",    "url": "https://feeds.reuters.com/reuters/worldNews"},
    {"name": "Reuters Business", "url": "https://feeds.reuters.com/reuters/businessNews"},
    {"name": "Reuters Tech",     "url": "https://feeds.reuters.com/reuters/technologyNews"},
    {"name": "Guardian World",   "url": "https://www.theguardian.com/world/rss"},
    {"name": "Guardian Business", "url": "https://www.theguardian.com/uk/business/rss"},
    {"name": "Guardian Tech",    "url": "https://www.theguardian.com/uk/technology/rss"},
    {"name": "Al Jazeera",       "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"name": "NPR News",         "url": "https://feeds.npr.org/1001/rss.xml"},
    {"name": "AP News",          "url": "https://rsshub.app/apnews/topics/world-news"},
    {"name": "FT World",         "url": "https://www.ft.com/world?format=rss"},
    {"name": "Economist",        "url": "https://www.economist.com/international/rss.xml"},
    {"name": "Ars Technica",     "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"name": "Nature News",      "url": "https://www.nature.com/nature.rss"},
    {"name": "Bloomberg",        "url": "https://feeds.bloomberg.com/markets/news.rss"},
]

GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID", "")

# Automation
AUTO_MONITOR_INTERVAL = int(os.getenv("AUTO_MONITOR_INTERVAL", "30"))  # minutes
AUTO_INGEST_HOUR = int(os.getenv("AUTO_INGEST_HOUR", "6"))  # daily at 6am
AUTO_GENERATE_THRESHOLD = float(os.getenv("AUTO_GENERATE_THRESHOLD", "0.7"))
AUTO_GENERATE_ENABLED = os.getenv("AUTO_GENERATE_ENABLED", "true").lower() == "true"
AUTO_CONFIRM_LEAD_HOURS = float(os.getenv("AUTO_CONFIRM_LEAD_HOURS", "2"))
AUTO_CONFIRM_THRESHOLD = float(os.getenv("AUTO_CONFIRM_THRESHOLD", "0.7"))
PRE_FILTER_ENABLED = os.getenv("PRE_FILTER_ENABLED", "true").lower() == "true"

# Timezone + engagement priors
USER_TIMEZONE = os.getenv("USER_TIMEZONE", "Europe/London")
PLATFORM_PRIORS = {
    "x": {8: 0.9, 9: 1.0, 12: 0.95, 13: 0.85, 17: 0.7, 18: 0.75, 19: 0.8},
    "linkedin": {7: 0.85, 8: 1.0, 9: 0.9, 12: 0.7, 17: 0.95, 18: 0.9},
}

FLASK_PORT = int(os.getenv("FLASK_PORT", "5050"))
