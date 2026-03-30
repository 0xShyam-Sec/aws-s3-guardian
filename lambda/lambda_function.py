import boto3
import uuid


def lambda_handler(event, context):
    s3 = boto3.client('s3')
    sns = boto3.client('sns')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('sentinel-findings')

    detail = event.get('detail', {})
    event_name = detail.get('eventName', 'Unknown')
    bucket = detail.get('requestParameters', {}).get('bucketName', 'Unknown')
    user = detail.get('userIdentity', {}).get('arn', 'Unknown')
    time = detail.get('eventTime', 'Unknown')
    region = detail.get('awsRegion', 'Unknown')
    source_ip = detail.get('sourceIPAddress', 'Unknown')
    event_source = detail.get('eventSource', 'Unknown')

    # Determine event category and severity
    if event_source == 's3.amazonaws.com':
        category = 'S3_PUBLIC_ACCESS'
        severity = 'HIGH'
    elif event_source == 'iam.amazonaws.com':
        category = 'IAM_CHANGE'
        if event_name in ['CreateUser', 'AttachUserPolicy', 'PutUserPolicy', 'CreateAccessKey']:
            severity = 'HIGH'
        else:
            severity = 'MEDIUM'
    elif event_source == 'ec2.amazonaws.com':
        category = 'NETWORK_CHANGE'
        severity = 'HIGH'
    elif event_source == 'cloudtrail.amazonaws.com':
        category = 'CLOUDTRAIL_TAMPERING'
        severity = 'CRITICAL'
    else:
        category = 'UNKNOWN'
        severity = 'LOW'

    # STEP 1: AUTO-REMEDIATE - Only for S3 public access events
    remediation_status = "N/A"
    if category == 'S3_PUBLIC_ACCESS':
        remediation_status = "FAILED"
        try:
            s3.put_public_access_block(
                Bucket=bucket,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
            remediation_status = "SUCCESS"
            print("REMEDIATED: Blocked public access on " + bucket)
        except Exception as e:
            remediation_status = "FAILED: " + str(e)
            print("REMEDIATION FAILED: " + str(e))

    # STEP 2: SEND FORMATTED EMAIL ALERT
    subject = "ALERT [" + severity + "]: " + event_name + " (" + category + ")"

    message = "========================================\n"
    message += "   PROJECT SENTINEL - SECURITY ALERT\n"
    message += "========================================\n\n"
    message += "Category:    " + category + "\n"
    message += "Severity:    " + severity + "\n"
    message += "Event:       " + event_name + "\n"
    message += "Resource:    " + bucket + "\n"
    message += "Time:        " + time + "\n"
    message += "Region:      " + region + "\n"
    message += "Source IP:   " + source_ip + "\n"
    message += "Changed By:  " + user + "\n\n"
    message += "----------------------------------------\n"
    message += "WHAT HAPPENED:\n"

    if category == 'S3_PUBLIC_ACCESS':
        if event_name == "PutBucketAcl":
            message += "Someone changed the bucket's access control list (ACL).\n"
            message += "This could make the bucket PUBLIC.\n"
        elif event_name == "PutBucketPolicy":
            message += "Someone changed the bucket's policy.\n"
            message += "This could allow unauthorized access.\n"
        elif event_name == "DeletePublicAccessBlock":
            message += "Someone removed the public access block.\n"
            message += "The bucket is now EXPOSED to being made public.\n"
    elif category == 'IAM_CHANGE':
        message += "IAM change detected: " + event_name + "\n"
        message += "Someone modified identity or access permissions.\n"
    elif category == 'NETWORK_CHANGE':
        message += "Network security change: " + event_name + "\n"
        message += "Someone modified security group rules.\n"
        message += "This could expose services to the internet.\n"
    elif category == 'CLOUDTRAIL_TAMPERING':
        message += "CRITICAL: CloudTrail tampering detected!\n"
        message += "Action: " + event_name + "\n"
        message += "Someone is trying to disable security logging.\n"
    else:
        message += "Action detected: " + event_name + "\n"

    message += "\n----------------------------------------\n"
    message += "AUTO-REMEDIATION:\n"
    if category == 'S3_PUBLIC_ACCESS':
        if remediation_status == "SUCCESS":
            message += "Status: FIXED AUTOMATICALLY\n"
            message += "Action: Public access has been BLOCKED on this bucket.\n"
            message += "All 4 public access block settings are now enabled.\n"
        else:
            message += "Status: REMEDIATION FAILED\n"
            message += "Error: " + remediation_status + "\n"
            message += "MANUAL ACTION REQUIRED - Please fix this immediately!\n"
    else:
        message += "Status: No auto-remediation for " + category + " events.\n"
        message += "MANUAL REVIEW REQUIRED.\n"

    message += "\n========================================\n"

    sns.publish(
        TopicArn='arn:aws:sns:us-east-1:629003556096:sentinel-alerts',
        Subject=subject[:100],
        Message=message
    )

    # Store finding in DynamoDB
    table.put_item(Item={
        'id': str(uuid.uuid4()),
        'timestamp': time,
        'eventName': event_name,
        'bucket': bucket,
        'severity': severity,
        'category': category,
        'status': remediation_status,
        'sourceIP': source_ip,
        'user': user
    })

    print("Alert sent for " + event_name + " on " + bucket)
    return {"statusCode": 200, "remediation": remediation_status}
