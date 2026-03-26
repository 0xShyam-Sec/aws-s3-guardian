output "s3_bucket_name" {
  value = aws_s3_bucket.monitored.id
}

output "lambda_function_name" {
  value = aws_lambda_function.sentinel.function_name
}

output "sns_topic_arn" {
  value = aws_sns_topic.sentinel_alerts.arn
}

output "cloudwatch_dashboard_url" {
  value = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=ProjectSentinel"
}
