# Production Readiness Matrix

| Component | Status | Test | Evidence | Known Limitation | Owner/Action |
| --- | --- | --- | --- | --- | --- |
| **AWS Infrastructure (VPC, ECS, ALB)** | STRUCTURALLY VERIFIED | Terraform `plan` & `validate` | `infra/environments/production` runs syntactically clean without public IP leaks | AWS credentials not provisioned locally; real traffic routing is untested physically | DevOps |
| **Database (PostgreSQL / RDS)** | VERIFIED | `test_db_failure_inject` | `/ready` handles connection drops with HTTP 503 rather than silent failures | Point-in-time restore is structural only (not real AWS) | DBA / DevOps |
| **Caching (ElastiCache Redis)** | VERIFIED | `test_redis_failure_inject` | Celery tasks and `/ready` handle socket timeouts safely without DB corruption | Multi-node failover untested | DevOps |
| **Browser Worker Idempotency** | VERIFIED | `test_browser_worker_crash_recovery_verify_state` | State Machine blocks `SUBMISSION_VERIFY -> SUBMITTING` bypass | Real Chromium OOM events must be tracked via CloudWatch | Backend |
| **Gmail Sync (historyId)** | VERIFIED | `fetch_new_messages` | Code uses `startHistoryId` and strictly commits after batch completion | `historyId` expires eventually, requiring full-sync fallback | Backend |
| **Web Push Delivery** | UNVERIFIED | Mock Push Provider used | Unit tests prove DB integrity and queue backoff logic | Safari/iOS device specific quirks untested | Frontend |
| **Deployment Automation (GitHub Actions)** | STRUCTURALLY VERIFIED | `deploy-production.yml` | Workflow executes OIDC assume-role logic | AWS OIDC provider not actually created | DevOps |
| **SSRF Protections** | VERIFIED | Playwright internal blocking | `127.0.0.1` and `169.254.169.254` filtered | DNS rebinding attacks require OS-level filtering | Security |
| **Kill Switches** | VERIFIED | `test_kill_switches` | Environment variables cleanly disable execution paths | N/A | DevOps / Backend |
