# AWS S3 Guardian

Automated security monitoring and remediation system for AWS S3 buckets. Detects unauthorized public access changes and **automatically fixes them** in real-time.

## What It Does

When someone makes an S3 bucket public (intentionally or by accident), this system:

1. **Detects** the change via CloudTrail + EventBridge
2. **Remediates** it instantly — Lambda blocks all public access
3. **Alerts** you with a clean formatted email
4. **Logs** everything to CloudWatch for auditing

```
Someone makes bucket public
        ↓
CloudTrail records the API call
        ↓
EventBridge matches the event pattern
        ↓
Lambda auto-remediates + sends alert email
        ↓
CloudWatch logs the event + dashboard updates
```

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────┐
│   S3 Bucket  │────▶│  CloudTrail  │────▶│  EventBridge    │
│  (monitored) │     │  (logs API   │     │  (matches rule) │
│              │     │   activity)  │     │                 │
└──────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                                                   ▼
┌──────────────┐     ┌──────────────┐     ┌─────────────────┐
│  CloudWatch  │◀────│     SNS      │◀────│     Lambda      │
│  (dashboard  │     │  (sends      │     │  (auto-fixes +  │
│   + alarms)  │     │   email)     │     │   formats alert)│
└──────────────┘     └──────────────┘     └─────────────────┘
```

## Events Monitored

| Event | Description |
|-------|-------------|
| `PutBucketAcl` | Bucket ACL changed (e.g., made public-read) |
| `PutBucketPolicy` | Bucket policy modified (could allow public access) |
| `DeletePublicAccessBlock` | Public access protections removed |

## Tech Stack

| Service | Purpose |
|---------|---------|
| AWS S3 | Monitored resource |
| AWS CloudTrail | API activity logging |
| AWS EventBridge | Event-driven rule matching |
| AWS Lambda (Python) | Auto-remediation + alert formatting |
| AWS SNS | Email notifications |
| AWS CloudWatch | Metrics, alarms, dashboard |
| Terraform | Infrastructure as Code |
| tfsec | Security scanning for Terraform |

## Project Structure

```
aws-s3-guardian/
├── lambda/
│   └── lambda_function.py      # Remediation + alert Lambda
├── terraform/
│   ├── main.tf                 # AWS provider config
│   ├── variables.tf            # Input variables
│   ├── s3.tf                   # S3 buckets + encryption + logging
│   ├── cloudtrail.tf           # CloudTrail setup
│   ├── sns.tf                  # SNS topic + email subscription
│   ├── lambda.tf               # Lambda + IAM (least privilege)
│   ├── eventbridge.tf          # Event rule + Lambda trigger
│   ├── cloudwatch.tf           # Dashboard + alarm + metric filter
│   └── outputs.tf              # Output values
```

## Deployment

### Prerequisites

- AWS account (Free Tier works)
- AWS CLI configured (`aws configure`)
- Terraform installed

### Deploy with Terraform

```bash
cd terraform
terraform init
terraform plan -var="alert_email=your@email.com"
terraform apply -var="alert_email=your@email.com"
```

### Destroy all resources

```bash
terraform destroy -var="alert_email=your@email.com"
```

## Security Features

- **Least privilege IAM** — Lambda only has `s3:PutBucketPublicAccessBlock` and `sns:Publish`
- **S3 encryption** — All buckets encrypted with AWS KMS
- **S3 versioning** — Enabled on all buckets
- **Public access blocked** — All buckets have public access block enabled
- **CloudTrail log validation** — Ensures logs haven't been tampered with
- **Multi-region trail** — Monitors API calls across all AWS regions
- **tfsec scanned** — 37 checks passed, 0 problems detected

## CloudWatch Dashboard

The `ProjectSentinel` dashboard shows:
- **S3 Violations Per Hour** — line chart of remediation events
- **Daily Violation Count** — total violations per day

An alarm triggers if **more than 3 violations occur in 1 hour**, indicating a potential attack.

## Sample Alert Email

```
========================================
   PROJECT SENTINEL - SECURITY ALERT
========================================

Event:       PutBucketAcl
Bucket:      my-bucket
Time:        2026-03-26T10:00:00Z
Region:      us-east-1
Source IP:    203.0.113.50
Changed By:  arn:aws:iam::123456789:user/someone

----------------------------------------
WHAT HAPPENED:
Someone changed the bucket's access control list (ACL).
This could make the bucket PUBLIC.

----------------------------------------
AUTO-REMEDIATION:
Status: FIXED AUTOMATICALLY
Action: Public access has been BLOCKED on this bucket.
All 4 public access block settings are now enabled.

========================================
```

## License

MIT
