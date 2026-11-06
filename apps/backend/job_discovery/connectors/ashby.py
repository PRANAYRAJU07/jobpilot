from typing import List, Dict, Any
from .base import JobSourceConnector, is_job_fresh
from bs4 import BeautifulSoup
from datetime import datetime

class AshbyConnector(JobSourceConnector):
    """
    Official Ashby ATS Public Job Board API Connector.
    Used by AI/tech companies such as OpenAI, Perplexity, Linear, Cohere, Ramp, etc.
    Endpoint: https://api.ashbyhq.com/posting-api/job-board/{external_company_id}
    """
    def discover_jobs(self) -> List[Dict[str, Any]]:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{self.external_company_id}?includeCompensation=true"
        response = self.client.get(url)
        response.raise_for_status()

        data = response.json()
        jobs_list = data.get("jobs", [])

        normalized_jobs = []
        for job in jobs_list:
            if job.get("isListed") is False:
                continue

            desc_plain = job.get("descriptionPlain") or ""
            if not desc_plain and job.get("descriptionHtml"):
                soup = BeautifulSoup(job["descriptionHtml"], "html.parser")
                desc_plain = soup.get_text(separator="\n", strip=True)

            published_str = job.get("publishedAt") or job.get("updatedAt")
            posted_at = None
            if published_str:
                try:
                    posted_at = datetime.fromisoformat(published_str.replace("Z", "+00:00")).replace(tzinfo=None)
                except ValueError:
                    pass

            job_url = job.get("jobUrl") or f"{self.career_url.rstrip('/')}/{job.get('id')}"
            apply_url = job.get("applyUrl") or job_url

            normalized_jobs.append({
                "external_job_id": str(job.get("id")),
                "source": "ASHBY",
                "company": self.company_name,
                "title": job.get("title", ""),
                "location": job.get("location", ""),
                "url": job_url,
                "apply_url": apply_url,
                "description": desc_plain,
                "employment_type": job.get("employmentType", ""),
                "posted_at": posted_at,
                "is_fresh": is_job_fresh(posted_at, max_age_hours=72),
                "raw_jd": job,
            })

        normalized_jobs.sort(key=lambda j: j.get("posted_at") or datetime.min, reverse=True)
        return normalized_jobs
