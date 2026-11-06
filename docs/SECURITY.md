# Application Security

## Operational Kill Switches
The JobPilot AI configuration includes absolute application kill-switches intended for emergency halting. These are configurable environment variables (passed to the ECS cluster):
- `APPLICATION_AUTOMATION_ENABLED`: Halts automated browser form filling.
- `GMAIL_SYNC_ENABLED`: Halts syncing of emails from Google API.
- `NOTIFICATIONS_ENABLED`: Disables Celery processing of outbound push notifications.

These switches will NOT destroy persisted data, they merely halt execution flows.

## Secret Management
- **GitHub Secrets:** Used exclusively for minor tokens. **AWS Access Keys are never stored here**. AWS IAM OIDC Federation handles short-lived deployment tokens.
- **Application Secrets:** `JWT_SECRET`, `VAPID_PRIVATE_KEY`, `ENCRYPTION_KEY`, and `DATABASE_URL` live strictly inside AWS Secrets Manager and are injected directly into the Fargate Task Execution environment. They never surface in `print()` statements, exceptions, or JSON API payloads.

## Inbound Defenses
- Strict **CORS** configurations block foreign domains (`*` is strictly disabled for authenticated routes).
- Endpoints susceptible to brute-forcing (`/api/config`, Login, Notification Subscriptions) are protected by explicit token-bucket Rate Limiting (`SlowAPI`).
- The Playwright worker blocks navigation to `localhost`, `169.254.169.254` (AWS Metadata), and arbitrary un-routed addresses to strictly prevent **SSRF** (Server-Side Request Forgery).
