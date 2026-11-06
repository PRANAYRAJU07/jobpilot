# Job Source Current State

## 1. What Already Exists
- **Database Schema (`models.py`)**: `Job` model exists with fields `id`, `external_job_id`, `source`, `title`, `company`, `location`, `status`, `raw_jd`, and `created_at`.
- **Job Engine (`job_engine.py`)**: Responsible for analyzing JDs, checking eligibility, and generating Truth Engine evidence.
- **Celery Infrastructure**: `celery_app.py`, `job_tasks.py`, `gmail_tasks.py` exist and are functioning.
- **Frontend Dashboard**: Basic UI is wired to display jobs, but relies on `job.url` and `job.description` which do not exist natively on the `Job` model.
- **WebSocket/Notifications**: Push notifications and live UI updates via `/ws`.

## 2. What is Incomplete
- **Job Source Connectors**: There are no actual mechanisms to populate the `Job` table autonomously.
- **Database Fields**: `Job` is missing crucial fields like `url`, `description`, `employment_type`, `posted_at`, and `updated_at`.
- **Source Registry**: No `JobSource` table exists to track which companies to monitor and their status/schedule.
- **Continuous Discovery**: No Celery Beat schedule is configured to poll job boards.

## 3. Existing Job Discovery Functionality
None. The system currently relies on manual ingestion or placeholders. The API `GET /api/jobs` just lists what's already in the DB.

## 4. Existing Celery Tasks
- `workers/tasks/job_tasks.py` contains basic task shells for processing jobs, but no discovery/polling loops.

## 5. Missing Source Connectors
- Greenhouse
- Lever
- Ashby
- Workday
- LinkedIn (Requires Partner Authorization)
- Generic Company Pages

## 6. Blockers & Required Changes
- Need to ALTER `jobs` table to include `url`, `description`, `employment_type`, and `posted_at`.
- Need to add `JobSource` model and `JobSourceConnector` framework to handle polling asynchronously.
- LinkedIn must remain documented as `AUTHORIZATION_REQUIRED` per official documentation prohibiting scraping.
