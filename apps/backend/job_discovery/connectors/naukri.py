from typing import List, Dict, Any
from .base import JobSourceConnector, is_job_fresh, parse_relative_time
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote_plus, urljoin
import json
import hashlib

class NaukriConnector(JobSourceConnector):
    """
    Discovers freshly posted jobs & internships from Naukri.com.
    Attempts Naukri's v3 search API with standard system headers, and falls back
    to Schema.org JSON-LD / HTML parsing from the public search page.
    `external_company_id` format: 'machine learning intern|hyderabad' or 'ai engineer fresher|india'
    """
    def discover_jobs(self) -> List[Dict[str, Any]]:
        query_spec = self.external_company_id or "machine learning intern|india"
        if "|" in query_spec:
            keywords, location = [p.strip() for p in query_spec.split("|", 1)]
        else:
            keywords, location = query_spec.strip(), "india"

        api_jobs = self._try_naukri_api(keywords, location)
        if api_jobs:
            return api_jobs

        return self._try_naukri_html(keywords, location)

    def _try_naukri_api(self, keywords: str, location: str) -> List[Dict[str, Any]]:
        api_url = (
            f"https://www.naukri.com/jobapi/v3/search"
            f"?noOfResults=25&urlType=search_by_key_loc&searchType=adv"
            f"&keyword={quote_plus(keywords)}&location={quote_plus(location)}"
            f"&freshness=3&sort=f"
        )
        headers = {
            "appid": "109",
            "systemid": "109",
            "Referer": "https://www.naukri.com/",
        }
        try:
            resp = self.client.get(api_url, headers=headers, timeout=15.0)
            if resp.status_code != 200:
                return []
            data = resp.json()
            job_details = data.get("jobDetails") or []
            normalized = []
            for jd in job_details:
                job_id = str(jd.get("jobId", ""))
                if not job_id:
                    continue
                title = jd.get("title", "")
                company = jd.get("companyName", "")
                jd_url = jd.get("jdURL", "")
                full_url = urljoin("https://www.naukri.com", jd_url) if jd_url else self.career_url

                placeholders = jd.get("placeholders") or []
                loc = next((p.get("label", "") for p in placeholders if p.get("type") == "location"), location)
                exp = next((p.get("label", "") for p in placeholders if p.get("type") == "experience"), "")

                created_ms = jd.get("createdDate")
                posted_at = datetime.utcfromtimestamp(created_ms / 1000.0) if created_ms else parse_relative_time(jd.get("footerPlaceholderLabel", "Today")) or datetime.utcnow()

                tags = jd.get("tagsAndSkills") or ""
                snippet = BeautifulSoup(jd.get("jobDescription", ""), "html.parser").get_text(" ", strip=True)
                description = f"{title} at {company}\nLocation: {loc}\nExperience: {exp}\nSkills: {tags}\n{snippet}"

                normalized.append({
                    "external_job_id": f"nk_{job_id}",
                    "source": "NAUKRI",
                    "company": company,
                    "title": title,
                    "location": loc,
                    "url": full_url,
                    "apply_url": full_url,
                    "description": description,
                    "employment_type": "INTERNSHIP" if "intern" in title.lower() else "FULL_TIME",
                    "posted_at": posted_at,
                    "is_fresh": is_job_fresh(posted_at, max_age_hours=72),
                    "raw_jd": jd,
                })
            return normalized
        except Exception:
            return []

    def _try_naukri_html(self, keywords: str, location: str) -> List[Dict[str, Any]]:
        slug_kw = keywords.lower().replace(" ", "-")
        slug_loc = location.lower().replace(" ", "-")
        page_url = self.career_url or f"https://www.naukri.com/{slug_kw}-jobs-in-{slug_loc}?freshness=3"
        try:
            resp = self.client.get(page_url, timeout=15.0)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.text, "html.parser")
            normalized = []
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    payload = json.loads(script.string or "{}")
                except Exception:
                    continue
                items = payload.get("itemListElement", []) if isinstance(payload, dict) else []
                for item in items:
                    url = item.get("url", "")
                    title = item.get("name", "")
                    if not url or not title:
                        continue
                    ext_id = hashlib.md5(url.encode()).hexdigest()[:14]
                    normalized.append({
                        "external_job_id": f"nk_{ext_id}",
                        "source": "NAUKRI",
                        "company": self.company_name or "Naukri Verified Employer",
                        "title": title,
                        "location": location.title(),
                        "url": url,
                        "apply_url": url,
                        "description": f"{title} ({keywords}) in {location.title()}",
                        "employment_type": "INTERNSHIP" if "intern" in title.lower() else "FULL_TIME",
                        "posted_at": datetime.utcnow(),
                        "is_fresh": True,
                        "raw_jd": item,
                    })
            return normalized
        except Exception:
            return []
