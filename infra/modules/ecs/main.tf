variable "environment" {}
variable "vpc_id" {}
variable "subnet_ids" {}
variable "db_secret_arn" {}
variable "redis_endpoint" {}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "jobpilot-${var.environment}"
}

# Task Execution Role (Pull image, push logs)
resource "aws_iam_role" "ecs_execution_role" {
  name = "jobpilot-${var.environment}-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Allow reading secrets for environment variables
resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name = "jobpilot-${var.environment}-execution-secrets"
  role = aws_iam_role.ecs_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          var.db_secret_arn,
          "arn:aws:secretsmanager:*:*:secret:jobpilot/${var.environment}/*"
        ]
      }
    ]
  })
}

# Task Role (App permissions like S3)
resource "aws_iam_role" "ecs_task_role" {
  name = "jobpilot-${var.environment}-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Example Service
resource "aws_ecs_service" "backend" {
  name            = "backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "jobpilot-${var.environment}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/jobpilot-backend:latest"
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
        }
      ]
      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = var.db_secret_arn
        }
      ]
    }
  ])
}

resource "aws_security_group" "ecs_tasks" {
  name   = "jobpilot-${var.environment}-ecs-tasks"
  vpc_id = var.vpc_id
}
