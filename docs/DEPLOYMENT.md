# Deployment Guide

## CI/CD Pipeline
JobPilot utilizes GitHub Actions for its CI/CD pipeline, defined in `.github/workflows/deploy-production.yml`.

Deployments to production require a Git push to `main` and successful execution of the continuous integration test suite (`tests/test_production_security.py`, `tests/test_notifications.py`, etc.).

### Pre-requisites
- AWS Account configured with OpenID Connect (OIDC) trust for the GitHub Actions IAM Role.
- Valid `VAPID_PRIVATE_KEY` stored in Secrets Manager.
- Valid `ENCRYPTION_KEY` stored in Secrets Manager.

### Deployment Steps
1. The GitHub action generates an immutable Docker image tagged by the Git SHA.
2. The image is pushed to the Amazon ECR repository.
3. The database migration is run using Alembic as a distinct AWS ECS RunTask call or Lambda.
4. If migrations succeed, an `aws ecs update-service` triggers a rolling update for the API, Worker, and Browser Worker task definitions.
5. ALB health checks monitor the `/api/health` and `/api/ready` endpoints.
6. The old tasks are completely drained before the new tasks go live.

### Local Infrastructure Provisioning
To manage infrastructure:
```bash
cd infra/environments/production
terraform init
terraform apply
```
**Important:** Do NOT commit `.tfstate` files to version control. They are backed remotely in the S3 backend configured in `main.tf`.
