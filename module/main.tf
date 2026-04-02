resource "aws_iam_role" "lambda_role" {
  name = var.lambda_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "custom-insights-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeVpcs"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "elasticloadbalancing:DescribeLoadBalancers",
          "cloudwatch:PutMetricData"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret",
          "secretsmanager:ListSecrets"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "cloudwatch:PutMetricData"
        ],
        Resource = "*",
        Condition = {
          StringEquals = {
            "cloudwatch:namespace" = "CustomInsights"
          }
        }
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.lambda_name}"
  retention_in_days = var.lambda_log_retention_days
}

resource "aws_lambda_function" "db_insights" {
  function_name = var.lambda_name
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  timeout       = 900
  memory_size   = 512

  filename         = data.external.zip_lambda_build.result.zip_path
  source_code_hash = data.external.zip_lambda_build.result.hash

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  environment {
    variables = {
      DB_SUFFIX         = var.db_suffix
      SECRET_SUFFIX     = var.secret_suffix
      THRESHOLD_MINUTES = var.threshold_minutes
      MAX_THREADS       = var.max_threads
    }
  }

  depends_on = [data.external.zip_lambda_build, aws_cloudwatch_log_group.lambda_logs]
}

resource "aws_scheduler_schedule" "db_scan_schedule" {
  name = "${var.lambda_name}-scheduler"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "rate(${var.scan_interval_hours} hours)"

  target {
    arn      = aws_lambda_function.db_insights.arn
    role_arn = aws_iam_role.scheduler_role.arn
  }
}

resource "aws_iam_role" "scheduler_role" {
  name = "${var.lambda_name}-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "scheduler.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "scheduler_policy" {
  role = aws_iam_role.scheduler_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Action = "lambda:InvokeFunction",
      Resource = "*"
    }]
  })
}

resource "aws_cloudwatch_metric_alarm" "stuck_queries_alarm" {
  alarm_name          = "Custom-Insights-StuckQueries"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = var.db_alarm_threshold
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "e1"
    return_data = true
    expression  = "SELECT MAX(StuckQueries) FROM SCHEMA(CustomInsights, DBInstanceIdentifier)"
    period      = var.scan_interval_hours * 3600
  }

  # No notifications for now
  alarm_actions             = []
  ok_actions                = []
  insufficient_data_actions = []
}

resource "aws_cloudwatch_metric_alarm" "container_restarts_alarm" {
  alarm_name          = "Custom-Insights-ContainerRestarts"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = var.container_restarts_alarm_threshold
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "e1"
    return_data = true
    expression  = "SELECT MAX(ContainerRestarts) FROM SCHEMA(CustomInsights, ALBName)"
    period      = var.scan_interval_hours * 3600
  }

  # No notifications for now
  alarm_actions             = []
  ok_actions                = []
  insufficient_data_actions = []
}