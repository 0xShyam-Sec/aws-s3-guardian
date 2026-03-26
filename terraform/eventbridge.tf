# EventBridge rule - detects S3 public access changes
resource "aws_cloudwatch_event_rule" "s3_public_access" {
  name        = "sentinel-s3-public-access"
  description = "Detects when S3 bucket permissions are changed"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["AWS API Call via CloudTrail"]
    detail = {
      eventSource = ["s3.amazonaws.com"]
      eventName   = ["PutBucketAcl", "PutBucketPolicy", "DeletePublicAccessBlock"]
    }
  })
}

# EventBridge target - triggers Lambda
resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.s3_public_access.name
  target_id = "sentinel-lambda"
  arn       = aws_lambda_function.sentinel.arn
}
