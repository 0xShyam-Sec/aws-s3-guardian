# Project Sentinel – Roadmap

## Prerequisites (Before You Start)
- AWS Free Tier account
- AWS CLI installed and configured
- Terraform installed
- Python 3.x (for Lambda)
- Basic understanding of AWS S3, IAM, and Lambda

---

## Week 1 – Foundation & Detection (Phases 1 & 2)

### Days 1–2: Environment Setup
- [x] Create an AWS account (Free Tier)
- [x] Create an S3 bucket (`project-sentinel-shyam-kakkad`) — this is your "monitored resource"
- [x] Enable **AWS CloudTrail** to log all API calls
- [x] Enable ACLs on bucket (needed for testing — newer buckets disable ACLs by default)
- [ ] Enable **S3 Server Access Logging**

### Days 3–4: Event Detection
- [x] Created **SNS Topic** (`sentinel-alerts`) with email subscription
- [x] Go to **Amazon EventBridge** → Created rule (`sentinel-s3-public-access`)
- [x] Set the trigger: `PutBucketAcl`, `PutBucketPolicy`, `DeletePublicAccessBlock`
- [x] Set the target: **SNS Topic** (email notification)
- [x] Tested: made S3 bucket public → confirmed email alert received

**Checkpoint:** You receive an email when the bucket goes public ✅ DONE

### Days 4.5: Email Formatter (Added Step)
- [x] Create a **Lambda function** (`sentinel-email-formatter`) in Python
- [x] Code it to: parse raw event → format clean readable email → send via SNS
- [x] Give Lambda **SNS publish permissions**
- [x] Update EventBridge rule target: Lambda instead of SNS directly
- [x] Test: make bucket public → receive clean formatted email

**Checkpoint:** Clean, readable alert emails instead of raw JSON ✅ DONE

---

## Week 2 – Remediation & Observability (Phases 3 & 4)

### Days 5–6: Lambda Remediation Function
- [x] Updated Lambda (`sentinel-email-formatter`) to auto-remediate + alert
- [x] Code: detects event → calls `put_public_access_block()` → restores private access → sends formatted email
- [x] IAM Role with S3 and SNS permissions attached
- [x] Increased Lambda timeout to 30 seconds
- [x] Tested: full end-to-end — violation → auto-fix → email confirms fix

**Checkpoint:** Full automated loop — violation → auto-fix → email alert ✅ DONE

```python
# Core logic of your Lambda
import boto3

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket = event['detail']['requestParameters']['bucketName']

    # Block all public access
    s3.put_public_access_block(
        Bucket=bucket,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
        }
    )
    print(f"REMEDIATED: Blocked public access on {bucket}")
```

### Days 7–8: Observability
- [x] CloudWatch Logs verified — Lambda logs automatically
- [x] Created **Metric Filter** (`sentinel-remediation-count`) — counts "REMEDIATED" events
- [x] Created **CloudWatch Alarm** (`sentinel-high-violation-rate`) — alerts if >3 violations in 1 hour
- [x] Created **CloudWatch Dashboard** (`ProjectSentinel`) — violations per hour + daily count

**Checkpoint:** Full automated loop — violation → auto-fix → logged → alerted ✅ DONE

---

## Week 3 – Governance & Polish (Phase 5)

### Days 9–10: Write Terraform Code
Convert everything you built manually into code:
- [ ] `s3.tf` — S3 bucket + access block config
- [ ] `cloudtrail.tf` — CloudTrail setup
- [ ] `eventbridge.tf` — Event rule + Lambda trigger
- [ ] `lambda.tf` — Lambda function + IAM role
- [ ] `cloudwatch.tf` — Dashboard + alarms

### Days 11–12: Policy as Code
- [ ] Install **tfsec** and run it on your Terraform code: `tfsec .`
- [ ] Fix any warnings it finds (e.g., encryption not enabled, logging missing)
- [ ] Optionally add an **OPA policy** to block deployment if S3 encryption is off

### Day 13–14: Final Deliverables
- [ ] Push everything to a **GitHub repo**
- [ ] Write a `README.md` with: what it does, architecture diagram, how to deploy
- [ ] Draw an architecture diagram (use draw.io or Excalidraw)
- [ ] Write a blog post on **Hashnode or dev.to** explaining your build
- [ ] Share on LinkedIn with `#DevSecBlueprint`

---

## Tools You Will Use

| Tool | Purpose | Free? |
|------|---------|-------|
| AWS S3 | The resource being monitored | Free tier |
| AWS CloudTrail | Logs all API activity | Free tier (first trail) |
| AWS EventBridge | Detects rule violations | Free tier |
| AWS Lambda | Auto-fixes violations | Free tier (1M requests/month) |
| AWS CloudWatch | Logs, dashboards, alerts | Free tier |
| AWS SNS | Email notifications | Free tier |
| AWS Secrets Manager | Stores credentials safely | ~$0.40/secret/month |
| Terraform | Writes infra as code | Free |
| tfsec | Scans Terraform for issues | Free |
| GitHub | Stores and versions code | Free |

---

## Key Things to Avoid (Common Mistakes)

- Never hardcode AWS keys in Lambda code — use IAM roles instead
- Don't give Lambda `AdministratorAccess` — only grant `s3:PutPublicAccessBlock` and `logs:*`
- Don't skip CloudTrail — without it, EventBridge can't see the events
- Don't forget to destroy resources after testing to avoid unexpected AWS charges
- New S3 buckets have ACLs disabled by default — enable them if testing with ACL changes

---

## Estimated Total Time
- Active setup & coding: ~20–25 hours
- Spread over 2–3 weeks comfortably
