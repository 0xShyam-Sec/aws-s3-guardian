# CloudTrail - logs all API activity
#tfsec:ignore:aws-cloudtrail-enable-at-rest-encryption -- KMS costs money, using S3 bucket encryption instead (free)
#tfsec:ignore:aws-cloudtrail-ensure-cloudwatch-integration -- CloudWatch Logs integration requires additional setup and costs
resource "aws_cloudtrail" "sentinel" {
  name                          = "sentinel-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail_logs.id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_logging                = true
  enable_log_file_validation    = true

  event_selector {
    read_write_type           = "All"
    include_management_events = true
  }

  depends_on = [aws_s3_bucket_policy.cloudtrail_logs]
}
