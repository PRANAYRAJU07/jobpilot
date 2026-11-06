from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime, timedelta
import re

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
}


def parse_relative_time(text: str) -> Optional[datetime]:
    """
    Converts relative freshness strings like 'Just now', '2 hours ago',
    'Today', '1 day ago', 'Few hours ago' into a UTC datetime.
    """
    if not text:
        return None
    t = text.strip().lower()
    now = datetime.utcnow()

    if any(k in t for k in ["just now", "moments ago", "few seconds", "active", "today", "few hours"]):
        return now - timedelta(hours=2)

    m_min = re.search(r"(\d+)\s*(?:min|minute)", t)
    if m_min:
        return now - timedelta(minutes=int(m_min.group(1)))

    m_hr = re.search(r"(\d+)\s*(?:hr|hour)", t)
    if m_hr:
        return now - timedelta(hours=int(m_hr.group(1)))

    if "yesterday" in t:
        return now - timedelta(days=1)

    m_day = re.search(r"(\d+)\s*day", t)
    if m_day:
        return now - timedelta(days=int(m_day.group(1)))

    m_wk = re.search(r"(\d+)\s*week", t)
    if m_wk:
        return now - timedelta(weeks=int(m_wk.group(1)))

    m_mo = re.search(r"(\d+)\s*month", t)
    if m_mo:
        return now - timedelta(days=30 * int(m_mo.group(1)))

    return None


def is_job_fresh(posted_at: Optional[datetime], max_age_hours: int = 72) -> bool:
    """
    Returns True if posted_at is within max_age_hours (default 72 hours / 3 days).
    """
    if not posted_at:
        return True
    naive_posted = posted_at.replace(tzinfo=None) if posted_at.tzinfo else posted_at
    age = datetime.utcnow() - naive_posted
    return age.total_seconds() <= max_age_hours * 3600


class JobSourceConnector(ABC):
    def __init__(self, company_name: str, external_company_id: str, career_url: str):
        self.company_name = company_name
        self.external_company_id = external_company_id
        self.career_url = career_url
        self.client = httpx.Client(timeout=30.0, headers=DEFAULT_HEADERS, follow_redirects=True)

    @abstractmethod
    def discover_jobs(self) -> List[Dict[str, Any]]:
        """
        Fetches jobs from the source and normalizes them into a standard dictionary:
        {
            "external_job_id": str,
            "source": str,
            "company": str,
            "title": str,
            "location": str,
            "url": str,
            "apply_url": str,
            "description": str,
            "employment_type": str,
            "posted_at": datetime or None,
            "is_fresh": bool,
            "raw_jd": dict
        }
        """
        pass

    def health_check(self) -> bool:
        return True
