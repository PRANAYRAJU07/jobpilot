# AWS Physical Verification Constraints

> **DISCLAIMER:** JobPilot AI was constructed within a local Docker sandbox. The codebase contains robust, structurally sound Terraform modules (`infra/environments/production`) designed specifically for AWS ECS Fargate, Amazon RDS, and ElastiCache Redis. However, actual AWS IAM permissions and root credentials were not provided to this AI context.

Consequently, per the strict mandates of Phase 13, all physical AWS provisioning is marked as **STRUCTURALLY VERIFIED** or **UNVERIFIED**.

## How to convert to VERIFIED

A human DevOps engineer must perform the following actions against an active AWS Account to transition this project to truly **VERIFIED** Production Ready status:

### 1. Terraform Initialization & Apply
```bash
export AWS_PROFILE=jobpilot-production
cd infra/environments/staging
terraform init
terraform apply
```
**Success Criteria:**
- The command successfully spins up the VPC, subnets, RDS, Redis, and ECS cluster without throwing IAM denied errors.
- The ALB issues an ACM certificate securely.

### 2. Network Isolation Verification
- Use AWS Reachability Analyzer.
- Attempt to route from the Internet Gateway directly to the RDS PostgreSQL port 5432.
**Success Criteria:**
- The trace must **FAIL**. The database must only be accessible from the ECS task security group.

### 3. Secrets Manager Integrity
- Inject real Google OAuth Client IDs and VAPID keys into AWS Secrets Manager.
- Boot the ECS tasks.
**Success Criteria:**
- Inspect CloudWatch logs. Ensure no `ENCRYPTION_KEY` or `JWT_SECRET` is printed during initialization tracebacks.

### 4. Database Restore Verification
- Wait for RDS to take its first automated backup.
- Execute a Point-In-Time Restore to a new identifier (`jobpilot-staging-restore-test`).
**Success Criteria:**
- The new database instance boots successfully.
- You can query `SELECT count(*) FROM users;` and receive valid output.

### 5. Push Notification Delivery
- Access the deployed Staging URL from a physical mobile device (e.g., iOS Safari).
- Grant Notification Permissions.
- Trigger a mock Interview detection.
**Success Criteria:**
- The physical device receives an OS-level push notification bridging the Web Push protocol through Apple/Google servers.
