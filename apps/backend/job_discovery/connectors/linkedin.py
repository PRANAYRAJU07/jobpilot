from typing import List, Dict, Any
from .base import JobSourceConnector, is_job_fresh, parse_relative_time
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote_plus, unquote, urlparse, parse_qs
import re

class LinkedInConnector(JobSourceConnector):
    """
    Discovers freshly posted jobs & internships from LinkedIn's public guest Jobs API.
    Supports query configuration via `external_company_id` (e.g. 'AI ML Intern|India' or 'Software Engineer Intern|Hyderabad, India')
    and fetches individual job detail pages to extract full descriptions and external company career page apply URLs.
    """
    def discover_jobs(self) -> List[Dict[str, Any]]:
        query_spec = self.external_company_id or "AI Machine Learning Intern|India"
        if "|" in query_spec:
            keywords, location = [p.strip() for p in query_spec.split("|", 1)]
        else:
            keywords, location = query_spec.strip(), "India"

        # f_TPR=r259200 filters to jobs posted within the last 72 hours (r86400 = 24 hours)
        search_url = (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={quote_plus(keywords)}&location={quote_plus(location)}"
            f"&f_TPR=r259200&sortBy=DD&start=0"
        )

        response = self.client.get(search_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        cards = soup.find_all("div", class_=re.compile(r"base-card|job-search-card"))
        if not cards:
            cards = soup.find_all("li")

        normalized_jobs = []
        for card in cards[:25]:
            urn = card.get("data-entity-urn", "")
            if not urn:
                urn_div = card.find(attrs={"data-entity-urn": True})
                urn = urn_div.get("data-entity-urn", "") if urn_div else ""

            job_id_match = re.search(r"jobPosting:(\d+)", urn)
            link_el = card.find("a", class_=re.compile(r"base-card__full-link")) or card.find("a", href=True)
            href = link_el["href"].split("?")[0] if link_el and link_el.get("href") else ""

            if not job_id_match and href:
                m_url = re.search(r"-(\d{7,})(?:$|\?)", href) or re.search(r"/view/(\d+)", href)
                ext_id = m_url.group(1) if m_url else href
            elif job_id_match:
                ext_id = job_id_match.group(1)
            else:
                continue

            title_el = card.find("h3", class_=re.compile(r"base-search-card__title")) or card.find("h3")
            company_el = card.find("h4", class_=re.compile(r"base-search-card__subtitle")) or card.find("h4")
            loc_el = card.find("span", class_=re.compile(r"job-search-card__location"))
            time_el = card.find("time")

            title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else self.company_name
            loc = loc_el.get_text(strip=True) if loc_el else location

            if not title or title == "***":
                continue

            posted_at = None
            if time_el:
                dt_attr = time_el.get("datetime")
                if dt_attr:
                    try:
                        posted_at = datetime.fromisoformat(dt_attr.replace("Z", "+00:00")).replace(tzinfo=None)
                    except ValueError:
                        pass
                if not posted_at:
                    posted_at = parse_relative_time(time_el.get_text(strip=True))

            posted_at = posted_at or datetime.utcnow()
            linkedin_url = href or f"https://www.linkedin.com/jobs/view/{ext_id}"

            # Fetch detail view for full description & external direct career apply URL
            description, apply_url, emp_type = self._fetch_job_detail(ext_id, linkedin_url, title, company)

            normalized_jobs.append({
                "external_job_id": f"li_{ext_id}",
                "source": "LINKEDIN",
                "company": company,
                "title": title,
                "location": loc,
                "url": linkedin_url,
                "apply_url": apply_url or linkedin_url,
                "description": description,
                "employment_type": emp_type or ("INTERNSHIP" if "intern" in title.lower() else "FULL_TIME"),
                "posted_at": posted_at,
                "is_fresh": is_job_fresh(posted_at, max_age_hours=72),
                "raw_jd": {
                    "linkedin_job_id": ext_id,
                    "search_keywords": keywords,
                    "original_apply_url": apply_url or linkedin_url,
                },
            })

        return normalized_jobs

    def _fetch_job_detail(self, job_id: str, fallback_url: str, title: str, company: str):
        detail_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        try:
            resp = self.client.get(detail_url, timeout=10.0)
            if resp.status_code != 200:
                return f"{title} at {company}", fallback_url, None

            soup = BeautifulSoup(resp.text, "html.parser")
            desc_div = soup.find("div", class_=re.compile(r"show-more-less-html__markup|description__text"))
            description = desc_div.get_text(separator="\n", strip=True) if desc_div else f"{title} at {company}"

            # Extract direct external company career URL if available
            apply_url = fallback_url
            apply_link = soup.find("a", class_=re.compile(r"apply-button")) or soup.find("a", href=re.compile(r"externalApply|url="))
            if apply_link and apply_link.get("href"):
                raw_href = apply_link["href"]
                parsed = urlparse(raw_href)
                qs = parse_qs(parsed.query)
                if "url" in qs and qs["url"]:
                    apply_url = unquote(qs["url"][0])
                elif raw_href.startswith("http"):
                    apply_url = raw_href

            emp_type = None
            for crit in soup.find_all("li", class_=re.compile(r"description__job-criteria-item")):
                header = crit.find("h3")
                val = crit.find("span")
                if header and val and "employment type" in header.get_text(strip=True).lower():
                    emp_type = val.get_text(strip=True)

            return description, apply_url, emp_type
        except Exception:
            return f"{title} at {company}", fallback_url, None
