terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.0"
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  default = "us-east-1"
}

variable "domain_name" {
  description = "Your domain name (e.g., api-orchestrator.com)"
  type        = string
}

variable "environment" {
  default = "production"
}

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "api-orchestrator-vpc"
    Environment = var.environment
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "api-orchestrator-igw"
  }
}

# Public Subnets for Load Balancer
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "api-orchestrator-public-${count.index + 1}"
    Type = "Public"
  }
}

# Private Subnets for Application
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "api-orchestrator-private-${count.index + 1}"
    Type = "Private"
  }
}

# RDS PostgreSQL Database
resource "aws_db_subnet_group" "main" {
  name       = "api-orchestrator-db-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "api-orchestrator-db-subnet-group"
  }
}

resource "aws_db_instance" "postgres" {
  identifier     = "api-orchestrator-db"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.medium"
  
  allocated_storage     = 100
  storage_type          = "gp3"
  storage_encrypted     = true
  
  db_name  = "api_orchestrator"
  username = "orchestrator_admin"
  password = random_password.db_password.result
  
  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  multi_az               = true
  deletion_protection    = true
  skip_final_snapshot    = false
  final_snapshot_identifier = "api-orchestrator-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  tags = {
    Name        = "api-orchestrator-database"
    Environment = var.environment
  }
}

# ElastiCache Redis for caching
resource "aws_elasticache_subnet_group" "main" {
  name       = "api-orchestrator-cache-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "api-orchestrator-redis"
  replication_group_description = "Redis cache for API Orchestrator"
  
  engine               = "redis"
  node_type            = "cache.r7g.large"
  number_cache_clusters = 2
  port                 = 6379
  
  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  automatic_failover_enabled = true
  multi_az_enabled          = true
  
  snapshot_retention_limit = 7
  snapshot_window          = "03:00-05:00"

  tags = {
    Name        = "api-orchestrator-redis"
    Environment = var.environment
  }
}

# ECS Cluster for containers
resource "aws_ecs_cluster" "main" {
  name = "api-orchestrator-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "api-orchestrator-ecs"
    Environment = var.environment
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "api-orchestrator-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = true
  enable_http2              = true
  enable_cross_zone_load_balancing = true

  tags = {
    Name        = "api-orchestrator-alb"
    Environment = var.environment
  }
}

# Route53 DNS
resource "aws_route53_zone" "main" {
  name = var.domain_name

  tags = {
    Name        = "api-orchestrator-zone"
    Environment = var.environment
  }
}

resource "aws_route53_record" "main" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "www" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "www.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# SSL Certificate
resource "aws_acm_certificate" "main" {
  domain_name               = var.domain_name
  subject_alternative_names = ["*.${var.domain_name}"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "api-orchestrator-cert"
    Environment = var.environment
  }
}

# Auto Scaling
resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = 20
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.main.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "cpu" {
  name               = "api-orchestrator-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# CloudWatch Monitoring
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "api-orchestrator-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", { stat = "Average" }],
            ["AWS/ECS", "MemoryUtilization", { stat = "Average" }],
            ["AWS/ApplicationELB", "TargetResponseTime", { stat = "Average" }],
            ["AWS/ApplicationELB", "RequestCount", { stat = "Sum" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "API Orchestrator Metrics"
        }
      }
    ]
  })
}

# Outputs
output "load_balancer_url" {
  value = aws_lb.main.dns_name
}

output "domain_name" {
  value = var.domain_name
}

output "database_endpoint" {
  value     = aws_db_instance.postgres.endpoint
  sensitive = true
}

output "redis_endpoint" {
  value     = aws_elasticache_replication_group.redis.primary_endpoint_address
  sensitive = true
}