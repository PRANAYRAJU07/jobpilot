# JobPilot AI — Staging Environment Runbook

## Overview
This runbook dictates operational procedures specifically for the JobPilot AWS Staging Environment (`jobpilot-staging`). Staging is intended to mimic production 1:1, specifically concerning isolation, network constraints, and failure recovery testing.

## Interacting with the Application
Because JobPilot strictly utilizes Docker Compose locally for development, staging deployments happen purely via GitHub Actions OIDC pipelines.
- **Triggering a Deploy**: Push code to the `main` branch. The Action (`.github/workflows/deploy-production.yml`) executes the ECR build and ECS rollout.
- **Monitoring Deployments**: Review the AWS ECS Console under `jobpilot-staging-cluster`. Ensure the API and Worker task definitions report `RUNNING`.
- **Database Migrations**: Migrations run explicitly in the pipeline. Do NOT run `alembic upgrade head` locally against the Staging RDS instance, as it is shielded in a private subnet.

## Simulating Failures (Chaos Testing)
As part of Phase 12 & 13 requirements, Staging must be resilient to failures.

### Database Unreachability
1. In the AWS Console, locate the `jobpilot-staging-db` Security Group.
2. Temporarily remove the Inbound rule allowing port 5432 from the ECS Tasks.
3. **Expected Behavior**: Celery queues will log errors but will NOT dequeue items permanently. The API `/api/ready` endpoint will fail, triggering ALB to 503 HTTP traffic cleanly.
4. **Recovery**: Restore the Security Group rule. Traffic should seamlessly resume.

### Worker Node Crashes
1. Manually Stop the ECS Task running the Browser Worker.
2. **Expected Behavior**: If a submission was in `SUBMISSION_VERIFY`, the state machine parks the state permanently. A replacement task will spin up but will **NOT** blindly click submit again.

### Kill Switches
Modify the AWS Secrets Manager / Environment Variables for the ECS service:
- Set `APPLICATION_AUTOMATION_ENABLED=false` to halt new browser tasks.
- Bounce the ECS tasks.
- Verify the PWA immediately reflects the disabled capability.

## Backup and Restore (RDS)
1. Navigate to AWS RDS -> Snapshots.
2. Select the latest automated snapshot for `jobpilot-staging`.
3. Choose "Restore to Point in Time" and spin up `jobpilot-staging-recovery`.
4. Connect via a bastion host or AWS Session Manager to verify the integrity of the data.
5. (Do NOT overwrite the active staging database during business hours).

## Accessing Logs
- All logs stream automatically via the `awslogs` driver to CloudWatch under `/ecs/jobpilot-staging`.
- No sensitive JWTs, tokens, or PII should be searchable.
