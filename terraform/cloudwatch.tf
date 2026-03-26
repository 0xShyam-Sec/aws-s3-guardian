# CloudWatch Log Group for Lambda
#tfsec:ignore:aws-cloudwatch-log-group-customer-key -- KMS encryption costs money, not needed for free tier
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/sentinel-email-formatter"
  retention_in_days = 14
}

# Metric Filter - counts remediation events
resource "aws_cloudwatch_log_metric_filter" "remediation_count" {
  name           = "sentinel-remediation-count"
  pattern        = "REMEDIATED"
  log_group_name = aws_cloudwatch_log_group.lambda_logs.name

  metric_transformation {
    name      = "RemediationCount"
    namespace = "ProjectSentinel"
    value     = "1"
  }
}

# Alarm - alerts if >3 violations in 1 hour
resource "aws_cloudwatch_metric_alarm" "high_violation_rate" {
  alarm_name          = "sentinel-high-violation-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "RemediationCount"
  namespace           = "ProjectSentinel"
  period              = 3600
  statistic           = "Sum"
  threshold           = 3
  alarm_description   = "Alerts when more than 3 S3 violations occur in 1 hour"
  alarm_actions       = [aws_sns_topic.sentinel_alerts.arn]
}

# Dashboard - violations over time
resource "aws_cloudwatch_dashboard" "sentinel" {
  dashboard_name = "ProjectSentinel"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 24
        height = 6
        properties = {
          metrics = [["ProjectSentinel", "RemediationCount", { stat = "Sum", period = 3600 }]]
          title   = "S3 Violations Per Hour"
          view    = "timeSeries"
          region  = var.aws_region
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [["ProjectSentinel", "RemediationCount", { stat = "Sum", period = 86400 }]]
          title   = "Daily Violation Count"
          view    = "singleValue"
          region  = var.aws_region
        }
      }
    ]
  })
}
