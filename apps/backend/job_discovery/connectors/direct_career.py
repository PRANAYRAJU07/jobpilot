from typing import List, Dict, Any
from .base import JobSourceConnector, is_job_fresh, parse_relative_time
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import json
import hashlib

class DirectCareerPageConnector(JobSourceConnector):
    """
    Discovers freshly posted jobs directly from original company career pages via:
    1. SmartRecruiters Public API (if career_url or external_company_id uses smartrecruiters:{company_id})
    2. Workday Public CXS API (if career_url is a myworkdayjobs.com portal)
    3. Schema.org JobPosting JSON-LD (<script type="application/ld+json">) embedded on official career pages
    4. RSS/Atom XML job feeds or structured career anchor links
    """
    def discover_jobs(self) -> List[Dict[str, Any]]:
        ext_id = (self.external_company_id or "").strip()
        if ext_id.lower().startswith("smartrecruiters:"):
            sr_company = ext_id.split(":", 1)[1].strip()
            return self._discover_smartrecruiters(sr_company)

        if "myworkdayjobs.com" in (self.career_url or "").lower():
            return self._discover_workday()

        return self._discover_html_or_jsonld()

    def _discover_smartrecruiters(self, sr_company: str) -> List[Dict[str, Any]]:
        url = f"https://api.smartrecruiters.com/v1/companies/{sr_company}/postings?limit=100"
        response = self.client.get(url)
        response.raise_for_status()
        data = response.json()
        postings = data.get("content", [])

        normalized = []
        for p in postings:
            released = p.get("releasedDate")
            posted_at = None
            if released:
                try:
                    posted_at = datetime.fromisoformat(released.replace("Z", "+00:00")).replace(tzinfo=None)
                except ValueError:
                    pass

            loc_obj = p.get("location") or {}
            loc_parts = [loc_obj.get("city"), loc_obj.get("region"), loc_obj.get("country")]
            loc_str = ", ".join([x for x in loc_parts if x])

            post_id = str(p.get("id") or p.get("uuid"))
            apply_url = f"https://jobs.smartrecruiters.com/{sr_company}/{post_id}"

            normalized.append({
                "external_job_id": post_id,
                "source": "DIRECT_CAREER",
                "company": self.company_name,
                "title": p.get("name", ""),
                "location": loc_str,
                "url": apply_url,
                "apply_url": apply_url,
                "description": f"{p.get('name', '')} at {self.company_name} ({loc_str}). Department: {(p.get('department') or {}).get('label', '')}",
                "employment_type": (p.get("typeOfEmployment") or {}).get("label", ""),
                "posted_at": posted_at,
                "is_fresh": is_job_fresh(posted_at, max_age_hours=72),
                "raw_jd": p,
            })
        return normalized

    def _discover_workday(self) -> List[Dict[str, Any]]:
        # Workday CXS JSON endpoint pattern: https://{tenant}.wdX.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
        response = self.client.post(
            self.career_url,
            json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""},
            headers={"Content-Type": "application/json", "Accept": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        postings = data.get("jobPostings", [])
        base_origin = self.career_url.split("/wday/cxs/")[0] if "/wday/cxs/" in self.career_url else self.career_url

        normalized = []
        for p in postings:
            posted_on = p.get("postedOn", "")
            posted_at = parse_relative_time(posted_on)
            ext_path = p.get("externalPath", "")
            job_url = urljoin(base_origin, ext_path) if ext_path else self.career_url
            bullet_fields = " | ".join(p.get("bulletFields") or [])

            normalized.append({
                "external_job_id": str(p.get("bulletFields", [ext_path])[0] if p.get("bulletFields") else ext_path),
                "source": "DIRECT_CAREER",
                "company": self.company_name,
                "title": p.get("title", ""),
                "location": p.get("locationsText", ""),
                "url": job_url,
                "apply_url": job_url,
                "description": f"{p.get('title', '')} - {bullet_fields}",
                "employment_type": "INTERNSHIP" if "intern" in (p.get("title", "")).lower() else "FULL_TIME",
                "posted_at": posted_at,
                "is_fresh": is_job_fresh(posted_at, max_age_hours=72),
                "raw_jd": p,
            })
        return normalized

    def _discover_html_or_jsonld(self) -> List[Dict[str, Any]]:
        response = self.client.get(self.career_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        normalized = []

        # 1. Extract Schema.org JobPosting JSON-LD blocks
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                payload = json.loads(script.string or "{}")
            except Exception:
                continue

            items = payload if isinstance(payload, list) else [payload]
            for item in items:
                if isinstance(item, dict) and item.get("@graph"):
                    items.extend(item["@graph"])
                if not isinstance(item, dict) or item.get("@type") != "JobPosting":
                    continue

                title = item.get("title", "")
                desc_html = item.get("description", "")
                clean_desc = BeautifulSoup(desc_html, "html.parser").get_text(separator="\n", strip=True) if desc_html else ""
                date_posted = item.get("datePosted")
                posted_at = None
                if date_posted:
                    try:
                        posted_at = datetime.fromisoformat(str(date_posted).replace("Z", "+00:00")).replace(tzinfo=None)
                    except ValueError:
                        posted_at = parse_relative_time(str(date_posted))

                job_url = item.get("url") or item.get("sameAs") or self.career_url
                job_url = urljoin(self.career_url, job_url)

                loc = ""
                job_loc = item.get("jobLocation")
                if isinstance(job_loc, dict):
                    addr = job_loc.get("address") or {}
                    if isinstance(addr, dict):
                        loc = ", ".join(filter(None, [addr.get("addressLocality"), addr.get("addressRegion"), addr.get("addressCountry")]))

                ext_id = str((item.get("identifier") or {}).get("value") or hashlib.md5(f"{title}:{job_url}".encode()).hexdigest()[:16])

                normalized.append({
                    "external_job_id": ext_id,
                    "source": "DIRECT_CAREER",
                    "company": self.company_name,
                    "title": title,
                    "location": loc,
                    "url": job_url,
                    "apply_url": job_url,
                    "description": clean_desc,
                    "employment_type": str(item.get("employmentType", "")),
                    "posted_at": posted_at,
                    "is_fresh": is_job_fresh(posted_at, max_age_hours=72),
                    "raw_jd": item,
                })

        # 2. Fallback: Extract structured career links if JSON-LD is not present
        if not normalized:
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                text = a_tag.get_text(" ", strip=True)
                if len(text) < 6 or len(text) > 120:
                    continue
                if any(k in href.lower() for k in ["/jobs/", "/careers/", "/positions/", "/openings/", "job-detail"]):
                    full_url = urljoin(self.career_url, href)
                    ext_id = hashlib.md5(full_url.encode()).hexdigest()[:16]
                    normalized.append({
                        "external_job_id": ext_id,
                        "source": "DIRECT_CAREER",
                        "company": self.company_name,
                        "title": text,
                        "location": "See Career Page",
                        "url": full_url,
                        "apply_url": full_url,
                        "description": f"{text} at {self.company_name}. Direct career listing from {full_url}",
                        "employment_type": "INTERNSHIP" if "intern" in text.lower() else "FULL_TIME",
                        "posted_at": datetime.utcnow(),
                        "is_fresh": True,
                        "raw_jd": {"title": text, "url": full_url},
                    })

        return normalized
