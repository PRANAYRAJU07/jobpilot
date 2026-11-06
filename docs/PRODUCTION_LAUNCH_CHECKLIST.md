# JobPilot AI — Production Launch Checklist

This gating matrix determines if the AWS Staging environment is ready to be promoted to Production and Automation can be safely enabled.

| Item | Status | Evidence | Owner | Remaining Action |
| --- | --- | --- | --- | --- |
| **Security - IAM Roles** | STRUCTURALLY VERIFIED | Terraform code uses `AmazonECSTaskExecutionRolePolicy` strictly | DevOps | Provision real AWS account and inspect console |
| **Security - Kill Switches** | VERIFIED | `test_kill_switches` proves `APPLICATION_AUTOMATION_ENABLED` operates dynamically | Backend | Keep Automation disabled by default at launch |
| **Infrastructure - VPC/ALB/ECS** | STRUCTURALLY VERIFIED | Terraform `plan` output | DevOps | Run `terraform apply` on physical infrastructure |
| **Secrets Manager** | UNVERIFIED | `modules/ecs/main.tf` defines the injection path | DevOps | Manually inject real OAuth tokens/VAPID into AWS Secrets Manager before boot |
| **Database (RDS)** | STRUCTURALLY VERIFIED | Terraform code maps DB into private subnets | DBA / DevOps | Execute Alembic migrations via AWS ECS RunTask after provisioning |
| **Redis (ElastiCache)** | STRUCTURALLY VERIFIED | Terraform code maps Redis into private subnets | DevOps | Ping test inside AWS VPC |
| **Browser Worker Isolation** | VERIFIED | `test_browser_worker_crash_recovery_verify_state` | Backend | Provision sufficient memory per task (2GB+) in AWS ECS |
| **Gmail OAuth** | UNVERIFIED | Code relies on valid Google Cloud Platform App credentials | Security | Approve Google App consent screen for production domain |
| **Push Notifications (Web Push)** | UNVERIFIED | Backend uses `pywebpush` properly per Phase 10 | Frontend | Generate real APNs/FCM tokens via production domain PWA |
| **Backups & Restore** | STRUCTURALLY VERIFIED | RDS PITR enabled in Terraform | DBA | **CRITICAL**: Perform an actual snapshot restore to a temporary RDS instance before launch |
| **Monitoring (CloudWatch)** | STRUCTURALLY VERIFIED | Terraform `aws_cloudwatch_log_group` attached to ECS | DevOps | Validate log correlation IDs on first run |
| **CI/CD** | STRUCTURALLY VERIFIED | `.github/workflows/deploy-production.yml` configured for OIDC | DevOps | Map GitHub repo in AWS IAM OIDC Provider |
| **Rollback** | UNVERIFIED | Code supports DB backward compatibility | DevOps | Perform a controlled rollback of the ECS service to `n-1` tag |

## Launch Sequence
1. Fulfill all `UNVERIFIED` and `STRUCTURALLY VERIFIED` requirements by executing them against the physical AWS Staging Account.
2. Update this document so all statuses are `VERIFIED`.
3. Set `APPLICATION_AUTOMATION_ENABLED=true` in AWS Secrets Manager / Environment Variables.
4. Route 53 domain flip.
