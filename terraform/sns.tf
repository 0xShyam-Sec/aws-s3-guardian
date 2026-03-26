# SNS Topic for security alerts
#tfsec:ignore:aws-sns-enable-topic-encryption -- KMS encryption costs money, not needed for free tier
resource "aws_sns_topic" "sentinel_alerts" {
  name = "sentinel-alerts"
}

# Email subscription
resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.sentinel_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}
