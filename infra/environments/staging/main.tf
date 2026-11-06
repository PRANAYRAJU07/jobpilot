terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    bucket         = "jobpilot-terraform-state-staging"
    key            = "staging/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-lock"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- VPC & NETWORKING ---
module "vpc" {
  source = "../../modules/vpc"

  environment = "staging"
  vpc_cidr    = "10.1.0.0/16"
  azs         = ["us-east-1a", "us-east-1b"]
}

# --- DATABASE (RDS) ---
module "rds" {
  source = "../../modules/rds"

  environment = "staging"
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnets

  instance_class = "db.t4g.micro"
  multi_az       = false
}

# --- REDIS (ElastiCache) ---
module "redis" {
  source = "../../modules/redis"

  environment = "staging"
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnets
}

# --- ECS CLUSTER & SERVICES ---
module "ecs" {
  source = "../../modules/ecs"

  environment = "staging"
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnets

  db_secret_arn  = module.rds.secret_arn
  redis_endpoint = module.redis.endpoint
}
