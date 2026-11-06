from typing import List, Dict, Any
from .base import JobSourceConnector, is_job_fresh
from bs4 import BeautifulSoup
from datetime import datetime
import html

class GreenhouseConnector(JobSourceConnector):
    def discover_jobs(self) -> List[Dict[str, Any]]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{self.external_company_id}/jobs?content=true"
        response = self.client.get(url)
        response.raise_for_status()

        data = response.json()
        jobs_list = data.get("jobs", [])

        normalized_jobs = []
        for job in jobs_list:
            desc_html = html.unescape(job.get("content", "") or "")
            soup = BeautifulSoup(desc_html, "html.parser") if desc_html else None
            clean_desc = soup.get_text(separator="\n", strip=True) if soup else ""

            updated_at_str = job.get("updated_at") or job.get("first_published")
            posted_at = None
            if updated_at_str:
                try:
                    posted_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                except ValueError:
                    pass

            direct_url = job.get("absolute_url", "")
            title = job.get("title", "")
            emp_type = "INTERNSHIP" if "intern" in title.lower() else "FULL_TIME"

            normalized_jobs.append({
                "external_job_id": str(job.get("id")),
                "source": "GREENHOUSE",
                "company": self.company_name,
                "title": title,
                "location": (job.get("location") or {}).get("name", ""),
                "url": direct_url,
                "apply_url": direct_url,
                "description": clean_desc,
                "employment_type": emp_type,
                "posted_at": posted_at,
                "is_fresh": is_job_fresh(posted_at, max_age_hours=72),
                "raw_jd": job,
            })

        # Sort newest first
        normalized_jobs.sort(key=lambda j: j.get("posted_at") or datetime.min, reverse=True)
        return normalized_jobs
