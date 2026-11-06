# Disaster Recovery Procedures

## Database (RDS PostgreSQL)
RDS automated backups are enabled with a retention period of 14 days and Point-in-Time Recovery (PITR) supported.

**Restoring:**
1. In the AWS RDS Console, select the `jobpilot-production` instance.
2. Select "Restore to point in time".
3. Verify application health using the staged cluster, then update the Secrets Manager `DATABASE_URL` value and bounce the ECS service.

## ElastiCache (Redis)
Redis operates purely as transient cache and Celery queue storage. In the event of a catastrophic regional failure:
1. Re-provision the module (`infra/modules/redis`).
2. Notifications and application states strictly rely on Postgres constraints, so no data drift will occur. Scheduled notifications will merely resume queueing.

## S3 (Resumes & Artifacts)
S3 Versioning is explicitly enabled on the `jobpilot-production-artifacts` bucket to prevent accidental deletions or overwrites of critical generated resumes and evidence screenshots.

## Missing VAPID / Encryption Keys
If the primary `ENCRYPTION_KEY` is lost, **all stored Gmail OAuth tokens will instantly invalidate**, requiring all users to hit the `/api/gmail/auth-url` endpoint to reconnect. Under no circumstances should the key be arbitrarily rotated without coordinated re-authorization workflows.
