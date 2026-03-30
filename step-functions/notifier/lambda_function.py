import boto3
import uuid


def lambda_handler(event, context):
    sns = boto3.client('sns')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('sentinel-findings')

    event_name = event.get('eventName', 'Unknown')
    bucket = event.get('bucket', 'Unknown')
    user = event.get('user', 'Unknown')
    time = event.get('timestamp', 'Unknown')
    region = event.get('region', 'Unknown')
    source_ip = event.get('sourceIP', 'Unknown')
    category = event.get('category', 'Unknown')
    severity = event.get('severity', 'Unknown')
    remediation_status = event.get('remediation_status', 'N/A')

    # Store in DynamoDB
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

    # Build email
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
            message += "Someone changed the bucket's ACL.\n"
            message += "This could make the bucket PUBLIC.\n"
        elif event_name == "PutBucketPolicy":
            message += "Someone changed the bucket's policy.\n"
            message += "This could allow unauthorized access.\n"
        elif event_name == "DeletePublicAccessBlock":
            message += "Someone removed the public access block.\n"
        else:
            message += "S3 security change detected.\n"
    elif category == 'IAM_CHANGE':
        message += "IAM change detected: " + event_name + "\n"
        message += "Someone modified identity or access permissions.\n"
    elif category == 'NETWORK_CHANGE':
        message += "Network security change: " + event_name + "\n"
        message += "Someone modified security group rules.\n"
    elif category == 'CLOUDTRAIL_TAMPERING':
        message += "CRITICAL: CloudTrail tampering detected!\n"
        message += "Action: " + event_name + "\n"
        message += "Someone is trying to disable security logging.\n"
    else:
        message += "Action detected: " + event_name + "\n"

    message += "\n----------------------------------------\n"
    message += "AUTO-REMEDIATION:\n"
    if remediation_status == 'SUCCESS':
        message += "Status: FIXED AUTOMATICALLY\n"
        message += "Public access has been BLOCKED on this bucket.\n"
    elif remediation_status == 'N/A':
        message += "Status: No auto-remediation for " + category + " events.\n"
        message += "MANUAL REVIEW REQUIRED.\n"
    else:
        message += "Status: REMEDIATION FAILED\n"
        message += "Error: " + remediation_status + "\n"
        message += "MANUAL ACTION REQUIRED!\n"

    message += "\n========================================\n"

    sns.publish(
        TopicArn='arn:aws:sns:us-east-1:629003556096:sentinel-alerts',
        Subject=subject[:100],
        Message=message
    )

    print("Alert sent for " + event_name + " (" + category + ")")
    return {'statusCode': 200, 'remediation': remediation_status}
