# JobPilot AI — Known Issues
*Last updated: 2026-09-22*

## Critical (Must fix before production)

None.

---

## High

### 1. Auto-application not end-to-end tested
**What:** The application state machine, browser automation worker (Playwright), and evidence storage are all implemented. However, no complete automated application workflow has been run through to `SUBMITTED` state against a permitted test site.  
**Impact:** Auto-apply cannot be enabled safely until this is verified.  
**Fix:** Run the mock career site test at `http://localhost:8002` through the full flow.

---

## Medium

### 2. Hyderabad-specific jobs: 0
**What:** The 18 new India-focused sources (Atlassian, Freshworks, Razorpay, CRED etc.) were added to the job source registry but their first scan has not yet completed.  
**Impact:** Dashboard shows 0 Hyderabad jobs.  
**Fix:** Wait for Celery Beat to run the discovery scan, or manually trigger: `docker exec jobpilot_backend python -c "from workers.celery_app import celery_app; celery_app.send_task('workers.tasks.run_discovery')"`

### 3. Gmail incremental sync (historyId) not tested
**What:** The OAuth connect flow is fixed. The first sync after connecting has not been verified.  
**Impact:** Email classification won't run until sync is tested.  
**Fix:** Connect Gmail, let initial sync run, verify emails appear in `/emails`.

### 4. Resume upload not implemented
**What:** The Resume page shows an empty state with no upload form.  
**Impact:** Tailored resume generation won't work until a master resume is uploaded.  
**Fix:** Implement a multipart/form-data upload endpoint and drag-drop UI.

### 5. Some new Greenhouse/Lever source IDs unverified
**What:** Source IDs like `amazon`, `microsoft`, `google` may not match the actual Greenhouse/Lever board slugs for those companies.  
**Impact:** First scan for those sources may return errors and set status=ERROR.  
**Fix:** If a source goes to ERROR status, verify its board URL manually and update `external_company_id`.

---

## Low

### 6. GMAIL_CLIENT_SECRET in docker-compose.yml
**What:** The Google OAuth credentials are stored directly in `docker-compose.yml`.  
**Impact:** Credentials visible in git history if committed.  
**Fix:** Move to a `.env` file and reference via `${GMAIL_CLIENT_SECRET}` in docker-compose. Add `.env` to `.gitignore`.

### 7. Browser hydration warning (fdprocessedid)
**What:** Browser password manager extensions inject `fdprocessedid` attributes into form fields before React hydrates.  
**Impact:** Development-only console warning. No user-visible effect.  
**Fix:** Suppress with `suppressHydrationWarning` on affected inputs, or disable extension on localhost.

### 8. Notifications table empty
**What:** 0 notifications in the database.  
**Impact:** Notifications page shows empty state.  
**Fix:** Will self-populate once applications are submitted or Gmail emails are classified.

### 9. `CandidateProfile.preferred_locations` type mismatch
**What:** DB column is `JSONB`, SQLAlchemy model doesn't have the new columns declared yet (subagent was updating this).  
**Impact:** Profile updates via API might not persist preference arrays until model is updated.  
**Fix:** Confirm subagent (94640824) completed models.py update; restart backend after.

---

## Confirmed Working

- ✓ `/api/health` and `/api/ready`
- ✓ User registration and login (JWT)
- ✓ Candidate profile creation and retrieval
- ✓ Job discovery (Greenhouse + Lever connectors)
- ✓ Job listing with India/internship/role_level filters
- ✓ Job stats including india_jobs, hyderabad_jobs, internship_jobs
- ✓ Job detail and Why This Job
- ✓ Gmail OAuth authorization URL generation (no PKCE)
- ✓ Gmail OAuth callback (direct token exchange)
- ✓ Notifications CRUD (read, mark read, preferences)
- ✓ Application events timeline
- ✓ WebSocket /ws endpoint
- ✓ Celery worker and Celery Beat running
- ✓ PostgreSQL + Redis healthy
- ✓ Frontend loading at http://localhost:3001
- ✓ Schema fully synchronized (56/56 checks pass)
