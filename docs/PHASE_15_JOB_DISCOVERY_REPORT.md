# Phase 15 — Real Job Discovery & Connectors Report

## 1. Existing Discovery Functionality
Prior to Phase 15, the `Job` model was barebones, and the system had **no actual automated job discovery**. The Celery task for discovery (`discover_jobs`) was a mocked placeholder returning a static dictionary.

## 2. Connectors Implemented
- **GreenhouseConnector**: Fetching and parsing HTML descriptions directly from the public `boards-api.greenhouse.io` endpoints.
- **LeverConnector**: Fetching and parsing from `api.lever.co/v0/postings`.
- **JobDiscoveryPipeline**: A pipeline handler providing unified normalization, deduplication (by `external_job_id` and `source`), and direct triggering of the Truth Engine via `JobEngineService.process_new_job`.

## 3. Connectors Not Implemented
- **Ashby / Generic HTML Scraper**: Did not force implementations per instruction.
- **Workday**: Workday instances are highly customized, often WAF-protected (Akamai), and thus marked as UNSUPPORTED natively.

## 4. Real Sources Tested & Seeded
The database was seeded with 8 tech companies. The following correctly resolved and fetched data:
- **Anthropic** (Greenhouse)
- **Stripe** (Greenhouse)
- **Databricks** (Greenhouse)
- **Robinhood** (Greenhouse)

*Note: OpenAI (Greenhouse), Figma, Notion, and Netflix (Lever) threw 404s, indicating they use custom ATS aliases. The system successfully caught these and updated their registry `status` to `ERROR`.*

## 5. Number of Real Jobs Retrieved
Over **2,316 raw jobs** were discovered from the 4 successful sources. Deduplication condensed this to **1,441 unique job records** securely inserted into the PostgreSQL `jobs` table.

## 6. Database Verification
- Used raw SQL `ALTER TABLE` to append `url`, `description`, `employment_type`, and `posted_at` to the `jobs` table without data loss.
- Created `JobSourceRegistry` to manage the polling status.

## 7. Deduplication Verification
The pipeline explicitly filters existing `external_job_id` and `source` tuples in PostgreSQL. Subsequent manual scans resulted in **0 duplicates**, correctly processing only new delta inserts.

## 8. Continuous Scheduling Verification
Configured a new `schedule_active_sources_task` in `celery_app.py` `beat_schedule` to execute every 5 minutes. Added the `beat` container to `docker-compose.yml`.

## 9. Source Health Monitoring
The pipeline successfully writes `jobs_found`, `status`, `last_error`, and timestamp records to `JobSourceRegistry`. This is actively tracking the 404 errors for the incorrect ATS aliases.

## 10. Frontend Integration
The `JobEngineService` was updated to output `eligibility_status` and `match_analysis` logic. `sources_router.py` was created to expose `/api/sources/` for the Source Dashboard. (Frontend Settings UI requires completion).

## 11. LinkedIn Authorization Status
**AUTHORIZATION REQUIRED**: LinkedIn strictly prohibits and rate-limits unauthenticated scraping. The official API requires an approved "Talent Solutions" partner program API Key. We will not scrape them.

## 12. API Credentials Required
None required for public Greenhouse and Lever endpoints.

## 13. Exact Next Steps
- Implement frontend UI in `/settings/job-sources` to interact with `GET /api/sources/` and `POST /api/sources/{id}/toggle`.
- Provide a candidate profile (currently `ANALYZED_NO_PROFILE`) to test the downstream semantic match engine.
- Proceed to Phase 16: Production Load Testing / AWS Staging.
