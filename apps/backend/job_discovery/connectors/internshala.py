from typing import List, Dict, Any
from .base import JobSourceConnector, is_job_fresh, parse_relative_time
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import re

class InternshalaConnector(JobSourceConnector):
    """
    Discovers freshly posted internships & fresher jobs from Internshala.
    `external_company_id` specifies the category slug, e.g.:
    - 'artificial-intelligence-ai-internship'
    - 'machine-learning-internship'
    - 'data-science-internship'
    - 'python-django-internship'
    - 'web-development-internship'
    """
    def discover_jobs(self) -> List[Dict[str, Any]]:
        slug = (self.external_company_id or "machine-learning-internship").strip("/")
        url = self.career_url if self.career_url and "internshala.com" in self.career_url else f"https://internshala.com/internships/{slug}/"

        response = self.client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        cards = soup.find_all("div", class_=re.compile(r"individual_internship"))
        normalized_jobs = []

        for card in cards[:30]:
            internship_id = card.get("internshipid")
            title_el = card.find(["h3", "a"], class_=re.compile(r"job-title-href|heading_4_5|profile"))
            if not title_el:
                continue

            link_el = title_el if title_el.name == "a" else title_el.find("a", href=True)
            if not link_el:
                link_el = card.find("a", class_=re.compile(r"job-title-href|view_detail_button"), href=True)

            href = link_el["href"] if link_el and link_el.get("href") else ""
            full_url = urljoin("https://internshala.com", href) if href else url

            if not internship_id:
                m_id = re.search(r"(\d{6,})", href)
                internship_id = m_id.group(1) if m_id else href

            if not internship_id:
                continue

            title = title_el.get_text(strip=True)
            company_el = card.find(["p", "div", "a"], class_=re.compile(r"company-name|company_name|heading_6"))
            company = company_el.get_text(strip=True) if company_el else "Internshala Partner Company"

            loc_el = card.find(["div", "span", "a"], class_=re.compile(r"locations|location_link"))
            location = loc_el.get_text(" ", strip=True) if loc_el else "India / Remote"

            stipend_el = card.find("span", class_=re.compile(r"stipend"))
            stipend = stipend_el.get_text(strip=True) if stipend_el else ""

            status_el = card.find("div", class_=re.compile(r"status-success|status-info|status-inactive|status"))
            freshness_text = status_el.get_text(strip=True) if status_el else "Today"
            posted_at = parse_relative_time(freshness_text) or datetime.utcnow()

            # Extract skill tags or description preview from card
            skill_tags = [
                s.get_text(strip=True)
                for s in card.find_all(["span", "div"], class_=re.compile(r"skill|tag|round_tabs"))
                if s.get_text(strip=True)
            ]
            card_text = card.get_text(separator=" | ", strip=True)
            desc_parts = [
                f"Role: {title} at {company}",
                f"Location: {location}",
                f"Stipend: {stipend}" if stipend else "",
                f"Skills: {', '.join(skill_tags)}" if skill_tags else "",
                f"Details: {card_text}",
            ]
            description = "\n".join([p for p in desc_parts if p])

            normalized_jobs.append({
                "external_job_id": f"is_{internship_id}",
                "source": "INTERNSHALA",
                "company": company,
                "title": title,
                "location": location,
                "url": full_url,
                "apply_url": full_url,
                "description": description,
                "employment_type": "INTERNSHIP",
                "posted_at": posted_at,
                "is_fresh": is_job_fresh(posted_at, max_age_hours=72),
                "raw_jd": {
                    "internship_id": str(internship_id),
                    "stipend": stipend,
                    "freshness_text": freshness_text,
                    "skills": skill_tags,
                    "original_apply_url": full_url,
                },
            })

        return normalized_jobs
