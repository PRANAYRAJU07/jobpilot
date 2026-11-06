#!/usr/bin/env python3
"""
Add real India-focused & Global job and internship sources across:
- Direct Company Career Boards (Greenhouse, Lever, Ashby, Direct Career)
- LinkedIn Fresh Jobs & Internships
- Internshala Internships (AI/ML, Data Science, Python, Software Engineering)
- Naukri Freshers & Internships
Safe to re-run (idempotent).
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
import models

INDIA_AND_PLATFORM_SOURCES = [
    # ── Popular Job & Internship Platforms (Fresh Listings) ──
    dict(company="LinkedIn — AI & ML Internships (India)", source_type="LINKEDIN",
         external_company_id="AI Machine Learning Intern|India",
         career_url="https://www.linkedin.com/jobs/search/?keywords=AI+Machine+Learning+Intern&location=India",
         country_focus="INDIA", tags=["linkedin", "india", "ai", "ml", "internship"]),
    dict(company="LinkedIn — Software Engineer Intern (Hyderabad)", source_type="LINKEDIN",
         external_company_id="Software Engineer Intern|Hyderabad, Telangana, India",
         career_url="https://www.linkedin.com/jobs/search/?keywords=Software+Engineer+Intern&location=Hyderabad",
         country_focus="INDIA", tags=["linkedin", "hyderabad", "software", "internship"]),
    dict(company="LinkedIn — GenAI & LLM Engineer (India)", source_type="LINKEDIN",
         external_company_id="Generative AI LLM Engineer|India",
         career_url="https://www.linkedin.com/jobs/search/?keywords=Generative+AI+LLM+Engineer&location=India",
         country_focus="INDIA", tags=["linkedin", "india", "llm", "genai"]),
    dict(company="Internshala — AI & Machine Learning Internships", source_type="INTERNSHALA",
         external_company_id="machine-learning-internship",
         career_url="https://internshala.com/internships/machine-learning-internship/",
         country_focus="INDIA", tags=["internshala", "india", "ml", "internship"]),
    dict(company="Internshala — Data Science Internships", source_type="INTERNSHALA",
         external_company_id="data-science-internship",
         career_url="https://internshala.com/internships/data-science-internship/",
         country_focus="INDIA", tags=["internshala", "india", "data-science", "internship"]),
    dict(company="Internshala — Python / FastAPI Internships", source_type="INTERNSHALA",
         external_company_id="python-django-internship",
         career_url="https://internshala.com/internships/python-django-internship/",
         country_focus="INDIA", tags=["internshala", "india", "python", "backend", "internship"]),
    dict(company="Naukri — AI/ML Intern & Fresher (India)", source_type="NAUKRI",
         external_company_id="machine learning intern|hyderabad",
         career_url="https://www.naukri.com/machine-learning-intern-jobs-in-hyderabad?freshness=3",
         country_focus="INDIA", tags=["naukri", "india", "hyderabad", "ml", "internship"]),
    dict(company="Naukri — Python Backend Fresher (India)", source_type="NAUKRI",
         external_company_id="python developer intern|india",
         career_url="https://www.naukri.com/python-developer-intern-jobs?freshness=3",
         country_focus="INDIA", tags=["naukri", "india", "python", "fresher"]),

    # ── Direct AI / Tech Company Career Pages (Ashby, Greenhouse, Lever) ──
    dict(company="OpenAI", source_type="ASHBY", external_company_id="openai",
         career_url="https://jobs.ashbyhq.com/openai", country_focus="GLOBAL",
         tags=["ai", "llm", "direct-career"]),
    dict(company="Perplexity AI", source_type="ASHBY", external_company_id="perplexity",
         career_url="https://jobs.ashbyhq.com/perplexity", country_focus="GLOBAL",
         tags=["ai", "llm", "search", "direct-career"]),
    dict(company="Linear", source_type="ASHBY", external_company_id="linear",
         career_url="https://jobs.ashbyhq.com/linear", country_focus="GLOBAL",
         tags=["saas", "engineering", "direct-career"]),
    dict(company="Anthropic", source_type="GREENHOUSE", external_company_id="anthropic",
         career_url="https://boards.greenhouse.io/anthropic", country_focus="GLOBAL",
         tags=["ai", "llm", "direct-career"]),
    dict(company="Databricks", source_type="GREENHOUSE", external_company_id="databricks",
         career_url="https://boards.greenhouse.io/databricks", country_focus="GLOBAL",
         tags=["data", "ai", "bengaluru", "direct-career"]),
    dict(company="Stripe", source_type="GREENHOUSE", external_company_id="stripe",
         career_url="https://boards.greenhouse.io/stripe", country_focus="GLOBAL",
         tags=["fintech", "bengaluru", "direct-career"]),
    dict(company="Atlassian", source_type="GREENHOUSE", external_company_id="atlassian",
         career_url="https://boards.greenhouse.io/atlassian", country_focus="INDIA",
         tags=["india", "bengaluru", "internship", "direct-career"]),
    dict(company="BrowserStack", source_type="GREENHOUSE", external_company_id="browserstack",
         career_url="https://boards.greenhouse.io/browserstack", country_focus="INDIA",
         tags=["india", "mumbai", "bengaluru", "direct-career"]),
    dict(company="Postman", source_type="GREENHOUSE", external_company_id="postman",
         career_url="https://boards.greenhouse.io/postman", country_focus="INDIA",
         tags=["india", "bengaluru", "internship", "direct-career"]),
    dict(company="Razorpay", source_type="GREENHOUSE", external_company_id="razorpaysoftwareprivatelimited",
         career_url="https://boards.greenhouse.io/razorpaysoftwareprivatelimited", country_focus="INDIA",
         tags=["india", "bengaluru", "fintech", "direct-career"]),
    dict(company="CRED", source_type="LEVER", external_company_id="cred",
         career_url="https://jobs.lever.co/cred", country_focus="INDIA",
         tags=["india", "bengaluru", "fintech", "direct-career"]),
    dict(company="PhonePe", source_type="GREENHOUSE", external_company_id="phonepe",
         career_url="https://boards.greenhouse.io/phonepe", country_focus="INDIA",
         tags=["india", "bengaluru", "fintech", "direct-career"]),
    dict(company="Zepto", source_type="LEVER", external_company_id="zepto",
         career_url="https://jobs.lever.co/zepto", country_focus="INDIA",
         tags=["india", "mumbai", "internship", "direct-career"]),
    dict(company="Meesho", source_type="LEVER", external_company_id="meesho",
         career_url="https://jobs.lever.co/meesho", country_focus="INDIA",
         tags=["india", "bengaluru", "direct-career"]),
    dict(company="Groww", source_type="LEVER", external_company_id="groww",
         career_url="https://jobs.lever.co/groww", country_focus="INDIA",
         tags=["india", "bengaluru", "fintech", "direct-career"]),
    dict(company="Cohere", source_type="ASHBY", external_company_id="cohere",
         career_url="https://jobs.ashbyhq.com/cohere", country_focus="GLOBAL",
         tags=["ai", "ml", "internship", "direct-career"]),
    dict(company="Mistral AI", source_type="LEVER", external_company_id="mistral",
         career_url="https://jobs.lever.co/mistral", country_focus="GLOBAL",
         tags=["ai", "ml", "llm", "direct-career"]),
    dict(company="Together AI", source_type="GREENHOUSE", external_company_id="togetherai",
         career_url="https://boards.greenhouse.io/togetherai", country_focus="GLOBAL",
         tags=["ai", "ml", "direct-career"]),
]


def main():
    db = SessionLocal()
    try:
        added = 0
        updated = 0
        for s in INDIA_AND_PLATFORM_SOURCES:
            existing = db.query(models.JobSourceRegistry).filter_by(
                company=s["company"]
            ).first()
            if existing:
                existing.source_type = s["source_type"]
                existing.external_company_id = s["external_company_id"]
                existing.career_url = s["career_url"]
                existing.status = "ACTIVE"
                existing.enabled = True
                updated += 1
                continue

            source = models.JobSourceRegistry(
                company=s["company"],
                source_type=s["source_type"],
                external_company_id=s["external_company_id"],
                career_url=s["career_url"],
                enabled=True,
                scan_interval_minutes=30,
                status="ACTIVE",
                country_focus=s.get("country_focus", "INDIA"),
                tags=s.get("tags", []),
            )
            db.add(source)
            added += 1
            print(f"  ADDED: {s['company']} ({s['source_type']})")

        db.commit()
        total = db.query(models.JobSourceRegistry).count()
        print(f"\nDone: {added} added, {updated} updated. Total sources now: {total}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
