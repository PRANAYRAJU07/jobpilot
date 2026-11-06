# AWS Architecture

## Overview
JobPilot AI runs natively on AWS ECS/Fargate to isolate browser dependencies from the web server and background job processors.

## Request Flow
1. **PWA (Frontend):** Served via Next.js directly or cached by CloudFront.
2. **API Traffic:** Handled by Route53 forwarding to an Application Load Balancer (ALB).
3. **Backend Services:** ECS Fargate tasks running FastAPI handle REST requests and websocket channels.
4. **Data Persistence:** PostgreSQL (Amazon RDS) is the single source of truth. Redis (ElastiCache) coordinates celery queues and WebSocket channels.
5. **Background Workers:** 
   - Celery handles rapid background async polling (Gmail sync, Notifications).
   - Playwright instances run strictly as distinct isolated tasks due to memory/CPU demands of Chromium.

## Network Security (VPC)
- **ALB** is public in public subnets.
- **ECS Tasks** run in private subnets with no inbound public access. NAT Gateways allow tasks to pull ECR images or reach external career sites.
- **RDS and ElastiCache** are in strictly isolated database subnets accessible *only* via security group rules mapped from the ECS Tasks.

## IAM Identity
- **Task Execution Role:** Used specifically by the ECS agent to fetch the image from ECR, retrieve `DATABASE_URL` and `VAPID_PRIVATE_KEY` directly from Secrets Manager, and stream `stdout` to CloudWatch.
- **Task Role:** Given to the application containers to reach S3 buckets and perform their duties (Least Privilege).
