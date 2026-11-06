# JobPilot AI — Full System Health Report
*Generated: 2026-09-22*

## Summary

| Status | Count |
|--------|-------|
| **Critical Errors Fixed** | 7 |
| **Database Columns Added** | 27 |
| **Schema Checks Passing** | 56/56 ✓ |
| **Backend Startup Errors** | 0 ✓ |

---

## Phase A — Initial Errors Discovered

| Error | Location | Root Cause |
|-------|----------|------------|
| `column gmail_connections.last_history_id does not exist` | Gmail page OAuth callback | Column in model but not in DB |
| `invalid_grant: Missing code verifier` | Gmail OAuth | `google-auth-oauthlib` added PKCE; reconstructed Flow lost the verifier |
| `inter is not defined` | `layout.tsx:19` | `Inter` font import stripped during edit |
| `localhost refused to connect` | localhost:3001 | Frontend dev server crashed due to Turbopack/webpack conflict |
| `Cannot find package 'next-pwa'` | next.config.mjs | next-pwa not installed in container |
| `ERR_MODULE_NOT_FOUND: next-pwa` | next.config.js | Built as .mjs but uses require() syntax |
| `NEXT_PUBLIC_API_URL` missing `/api` | All frontend API calls | docker-compose env was `http://localhost:8001` not `http://localhost:8001/api` |

---

## Phase B — Database Schema Drift

### `gmail_connections`
| Column | Model | DB Before | DB After |
|--------|-------|-----------|----------|
| `last_history_id` | ✓ | ✗ MISSING | ✓ Added |

### `applications`
| Column | Model | DB Before | DB After |
|--------|-------|-----------|----------|
| `created_at` | ✓ | ✗ | ✓ Added |
| `updated_at` | ✓ | ✗ | ✓ Added |
| `error_message` | ✓ | ✗ | ✓ Added |
| `error_type` | ✓ | ✗ | ✓ Added |
| `retry_count` | ✓ | ✗ | ✓ Added |

### `jobs` (new classification columns)
| Column | Purpose | DB After |
|--------|---------|----------|
| `country` | India/USA/Remote | ✓ Added |
| `region` | City name | ✓ Added |
| `role_level` | INTERN/JUNIOR/SENIOR | ✓ Added |
| `is_internship` | Boolean flag | ✓ Added |
| `eligibility_status` | ELIGIBLE/NOT_ELIGIBLE/UNKNOWN | ✓ Added |
| `graduation_year_min` | Year range min | ✓ Added |
| `graduation_year_max` | Year range max | ✓ Added |

### `candidate_profiles` (preference columns)
| Column | DB After |
|--------|----------|
| `location` | ✓ Added |
| `preferred_locations` | ✓ Added |
| `preferred_roles` | ✓ Added |
| `preferred_job_types` | ✓ Added |
| `min_match_score` | ✓ Added |
| `daily_application_limit` | ✓ Added |
| `auto_apply_enabled` | ✓ Added |
| `created_at` / `updated_at` | ✓ Added |

### `job_source_registry`
| Column | DB After |
|--------|----------|
| `country_focus` | ✓ Added |
| `tags` | ✓ Added |

---

## Phase C — Migration System

- Created `apps/backend/scripts/migrate_schema.py` — idempotent migration runner
- Created `apps/backend/scripts/check_db_schema.py` — schema verification
- **Result: 56/56 column checks pass**

---

## Phase D — DB Reset/Rebuild Option

```powershell
# DESTRUCTIVE — destroys all data! Use only in development.
docker compose down -v
docker compose up -d
docker exec jobpilot_backend python scripts/migrate_schema.py
docker exec jobpilot_backend python scripts/seed_india_sources.py
```

---

## Phase E — Backend Error Scan

| Check | Result |
|-------|--------|
| Backend startup | ✓ No errors |
| `/api/health` | ✓ `{"status":"ok"}` |
| `/api/ready` | ✓ `{"status":"ready"}` |
| PostgreSQL | ✓ Healthy |
| Redis | ✓ Healthy |
| Celery worker | ✓ Running |
| Celery Beat | ✓ Running |

---

## Phase F — Gmail Integration

**Root cause of `invalid_grant`:** `google-auth-oauthlib`'s `Flow` class auto-generates PKCE `code_verifier` when building the auth URL. When the callback endpoint reconstructed a new `Flow` object, it lost the verifier, causing Google to reject the token exchange.

**Fix applied:**
- Removed `Flow` entirely from auth URL generation and callback
- Auth URL built manually with direct HTTP parameters (no PKCE)
- Token exchange done via direct `POST` to `https://oauth2.googleapis.com/token`
- Email address fetched via `GET https://www.googleapis.com/oauth2/v2/userinfo`
- State stored in Redis with 10-minute TTL for CSRF protection
- `token_expires_at` correctly derived from `expires_in` in token response
- No `connected_at` field used (doesn't exist in model)

**OAuth Redirect URI:** `http://localhost:8001/api/gmail/callback`  
*(Must be added to Google Cloud Console → Credentials → Authorized redirect URIs)*

---

## Phase I-J — India Job Statistics (Real, Verified)

| Metric | Count |
|--------|-------|
| Total jobs in DB | **2,474** |
| India-tagged jobs | **146** |
| Hyderabad jobs | **0** *(existing sources don't post Hyderabad-specific roles)* |
| Internship jobs | **76** |
| 2027-eligible jobs | **21** |
| Entry-level jobs (Intern/Fresher/Junior) | **864** |

> **Note:** 0 Hyderabad jobs reflects that the current Greenhouse/Lever sources (Stripe, Anthropic, Databricks etc.) don't post India-specific roles. The new India-focused sources added will fix this on the next scan.

---

## Phase K — Job Sources

| Company | Type | Status |
|---------|------|--------|
| Atlassian | GREENHOUSE | ACTIVE |
| BrowserStack | GREENHOUSE | ACTIVE |
| Postman | GREENHOUSE | ACTIVE |
| Freshworks | GREENHOUSE | ACTIVE |
| Razorpay | LEVER | ACTIVE |
| CRED | LEVER | ACTIVE |
| PhonePe | GREENHOUSE | ACTIVE |
| Zepto | LEVER | ACTIVE |
| Meesho | GREENHOUSE | ACTIVE |
| Groww | LEVER | ACTIVE |
| Google | LEVER | ACTIVE |
| Microsoft | GREENHOUSE | ACTIVE |
| Amazon | GREENHOUSE | ACTIVE |
| Salesforce | GREENHOUSE | ACTIVE |
| Cohere | GREENHOUSE | ACTIVE |
| Mistral AI | LEVER | ACTIVE |
| Hugging Face | LEVER | ACTIVE |
| Together AI | GREENHOUSE | ACTIVE |

**Total active sources: 23** (up from 5)

---

## Phase L — Candidate Profile (M Pranay Raju)

| Field | Value |
|-------|-------|
| Name | M Pranay Raju |
| Email | sailajamalli2006@gmail.com |
| University | Malla Reddy University |
| Degree | B.Tech CSE (AI & ML) |
| CGPA | 8.92 |
| Graduation Year | 2027 |
| Location | Hyderabad, India |
| Skills | 37 (Python, PyTorch, TensorFlow, LLMs, RAG, FastAPI, etc.) |
| Projects | 4 (ASFO, RAG QA, CV Detection, Knowledge Graph) |
| Auto-apply | Disabled (default) |
| Daily limit | 10 applications |

---

## Phase O — Application Automation Status

| Component | Status |
|-----------|--------|
| Application state machine (DISCOVERED → SUBMITTED) | ✓ Implemented in models |
| ApplicationEvent timeline | ✓ DB table exists |
| SubmissionEvidence storage | ✓ DB table exists |
| Browser worker (Playwright) | ✓ Container running |
| Auto-submit policy | ✓ DISABLED by default |
| Daily application limit | ✓ Configurable (default: 10) |
| CAPTCHA/OTP detection | ✓ States: CAPTCHA_REQUIRED, OTP_REQUIRED |
| Unknown question handling | ✓ State: UNKNOWN_QUESTION |

> **Note:** Auto-application workflow has NOT been tested against a live employer. The state machine, evidence storage, and safety guards are implemented. Testing against the local mock site is required before enabling AUTO mode.

---

## Phase X — Notifications

| Feature | Status |
|---------|--------|
| In-app notifications | ✓ Working (notifications table) |
| Mark read / mark all read | ✓ Working |
| Notification preferences | ✓ Working |
| Web Push subscriptions | ✓ DB table exists |
| Email notifications | Disabled (no SMTP configured) |
| `read` boolean field | ✓ Fixed — computed from `read_at` |

---

## Phase AC — Security

| Check | Status |
|-------|--------|
| JWT auth | ✓ Active |
| Password hashing (bcrypt) | ✓ Active |
| CORS — strict origin | ✓ `FRONTEND_URL` only |
| OAuth 2.0 (Google) | ✓ Fixed |
| Token NEVER logged | ✓ Verified in code |
| SQL injection | ✓ SQLAlchemy parameterized queries |
| Multi-user data isolation | ✓ All queries filter by `user_id` |
| `GMAIL_CLIENT_SECRET` in logs | ✗ Present in docker-compose.yml (move to .env file before production) |

---

## Phase AD — Remaining Known Issues

| Issue | Severity | Notes |
|-------|----------|-------|
| Hyderabad-specific jobs: 0 | Medium | New India sources added — next scan will pull India jobs |
| Auto-application not E2E tested | High | Browser worker running; needs mock site test |
| Gmail sync (historyId update) not tested | Medium | OAuth flow fixed; incremental sync logic needs test |
| Resume upload not implemented | Medium | UI shows empty state; needs file upload endpoint |
| Google/Microsoft/Amazon Greenhouse IDs unverified | Medium | May fail on first scan — need to verify board slugs |
| `GMAIL_CLIENT_SECRET` in docker-compose | Low | Move to `.env` file before sharing/committing |
| Notifications table has 0 rows | Low | Will populate once applications/Gmail events fire |

---

## Exact Commands to Run Locally

```powershell
# Start everything
cd "c:\Users\prana\OneDrive\Desktop\job pilot\jobpilot-ai"
docker compose up -d

# Verify schema
docker exec jobpilot_backend python scripts/check_db_schema.py

# Run migration if needed
docker exec jobpilot_backend python scripts/migrate_schema.py

# Classify existing jobs
docker exec jobpilot_backend python scripts/classify_existing_jobs.py

# Seed India sources
docker exec jobpilot_backend python scripts/seed_india_sources.py
```

**Localhost URL:** http://localhost:3001  
**API:** http://localhost:8001/api  
**API Docs:** http://localhost:8001/docs

---

## Confirmation

- ✓ AWS NOT deployed
- ✓ No real employer applications submitted
- ✓ No fake jobs created
- ✓ No invented candidate information
- ✓ Schema fully synchronized (56/56 checks pass)
- ✓ Gmail OAuth fixed (no PKCE, direct token exchange)
- ✓ Pranay's real profile seeded with verified skills/projects
- ✓ 18 India/global sources added to discovery queue
