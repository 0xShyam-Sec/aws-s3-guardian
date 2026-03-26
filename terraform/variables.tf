variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  default     = "project-sentinel"
}

variable "bucket_name" {
  description = "Name of the S3 bucket to monitor"
  default     = "project-sentinel-shyam-kakkad"
}

variable "alert_email" {
  description = "Email address for security alerts"
  type        = string
}
