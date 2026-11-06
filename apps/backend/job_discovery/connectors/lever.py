from typing import List, Dict, Any
from .base import JobSourceConnector, is_job_fresh
from datetime import datetime

class LeverConnector(JobSourceConnector):
    def discover_jobs(self) -> List[Dict[str, Any]]:
        url = f"https://api.lever.co/v0/postings/{self.external_company_id}?mode=json"
        response = self.client.get(url)
        response.raise_for_status()

        jobs_list = response.json()
        if not isinstance(jobs_list, list):
            return []

        normalized_jobs = []
        for job in jobs_list:
            created_at_ms = job.get("createdAt")
            posted_at = None
            if created_at_ms:
                posted_at = datetime.utcfromtimestamp(created_at_ms / 1000.0)

            hosted_url = job.get("hostedUrl", "")
            apply_url = job.get("applyUrl") or hosted_url
            categories = job.get("categories") or {}
            lists_text = "\n".join(
                f"{item.get('text', '')}: {item.get('content', '')}"
                for item in (job.get("lists") or [])
                if isinstance(item, dict)
            )
            full_desc = "\n".join(
                part for part in [
                    job.get("descriptionPlain", "") or job.get("description", ""),
                    lists_text,
                    job.get("additionalPlain", ""),
                ] if part
            )

            normalized_jobs.append({
                "external_job_id": str(job.get("id")),
                "source": "LEVER",
                "company": self.company_name,
                "title": job.get("text", ""),
                "location": categories.get("location", "") or categories.get("allLocations", [""])[0] if isinstance(categories.get("allLocations"), list) else categories.get("location", ""),
                "url": hosted_url,
                "apply_url": apply_url,
                "description": full_desc,
                "employment_type": categories.get("commitment", ""),
                "posted_at": posted_at,
                "is_fresh": is_job_fresh(posted_at, max_age_hours=72),
                "raw_jd": job,
            })

        normalized_jobs.sort(key=lambda j: j.get("posted_at") or datetime.min, reverse=True)
        return normalized_jobs
