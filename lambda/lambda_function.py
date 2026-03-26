import boto3


def lambda_handler(event, context):
    s3 = boto3.client('s3')
    sns = boto3.client('sns')

    detail = event.get('detail', {})
    event_name = detail.get('eventName', 'Unknown')
    bucket = detail.get('requestParameters', {}).get('bucketName', 'Unknown')
    user = detail.get('userIdentity', {}).get('arn', 'Unknown')
    time = detail.get('eventTime', 'Unknown')
    region = detail.get('awsRegion', 'Unknown')
    source_ip = detail.get('sourceIPAddress', 'Unknown')

    # STEP 1: AUTO-REMEDIATE - Block all public access
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
    subject = "ALERT: " + event_name + " on " + bucket + " [" + remediation_status + "]"

    message = "========================================\n"
    message += "   PROJECT SENTINEL - SECURITY ALERT\n"
    message += "========================================\n\n"
    message += "Event:       " + event_name + "\n"
    message += "Bucket:      " + bucket + "\n"
    message += "Time:        " + time + "\n"
    message += "Region:      " + region + "\n"
    message += "Source IP:   " + source_ip + "\n"
    message += "Changed By:  " + user + "\n\n"
    message += "----------------------------------------\n"
    message += "WHAT HAPPENED:\n"

    if event_name == "PutBucketAcl":
        message += "Someone changed the bucket's access control list (ACL).\n"
        message += "This could make the bucket PUBLIC.\n"
    elif event_name == "PutBucketPolicy":
        message += "Someone changed the bucket's policy.\n"
        message += "This could allow unauthorized access.\n"
    elif event_name == "DeletePublicAccessBlock":
        message += "Someone removed the public access block.\n"
        message += "The bucket is now EXPOSED to being made public.\n"
    else:
        message += "Action detected: " + event_name + "\n"

    message += "\n----------------------------------------\n"
    message += "AUTO-REMEDIATION:\n"
    if remediation_status == "SUCCESS":
        message += "Status: FIXED AUTOMATICALLY\n"
        message += "Action: Public access has been BLOCKED on this bucket.\n"
        message += "All 4 public access block settings are now enabled.\n"
    else:
        message += "Status: REMEDIATION FAILED\n"
        message += "Error: " + remediation_status + "\n"
        message += "MANUAL ACTION REQUIRED - Please fix this immediately!\n"

    message += "\n========================================\n"

    sns.publish(
        TopicArn='arn:aws:sns:us-east-1:629003556096:sentinel-alerts',
        Subject=subject[:100],
        Message=message
    )

    print("Alert sent for " + event_name + " on " + bucket)
    return {"statusCode": 200, "remediation": remediation_status}
