def lambda_handler(event, context):
    detail = event.get('detail', {})
    event_name = detail.get('eventName', 'Unknown')
    event_source = detail.get('eventSource', 'Unknown')
    bucket = detail.get('requestParameters', {}).get('bucketName', 'Unknown')
    user = detail.get('userIdentity', {}).get('arn', 'Unknown')
    time = detail.get('eventTime', 'Unknown')
    region = detail.get('awsRegion', 'Unknown')
    source_ip = detail.get('sourceIPAddress', 'Unknown')

    # Classify category and severity
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

    return {
        'eventName': event_name,
        'eventSource': event_source,
        'bucket': bucket,
        'user': user,
        'timestamp': time,
        'region': region,
        'sourceIP': source_ip,
        'category': category,
        'severity': severity
    }
