import boto3


def lambda_handler(event, context):
    s3 = boto3.client('s3')
    cloudtrail = boto3.client('cloudtrail', region_name='us-east-2')
    category = event.get('category', '')
    bucket = event.get('bucket', '')
    event_name = event.get('eventName', '')

    # S3 PUBLIC ACCESS — block public access
    if category == 'S3_PUBLIC_ACCESS':
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
            event['remediation_status'] = 'SUCCESS'
            print("REMEDIATED: Blocked public access on " + bucket)
        except Exception as e:
            event['remediation_status'] = 'FAILED: ' + str(e)
            print("REMEDIATION FAILED: " + str(e))

    # CLOUDTRAIL TAMPERING — re-enable logging
    elif category == 'CLOUDTRAIL_TAMPERING':
        if event_name == 'StopLogging':
            try:
                cloudtrail.start_logging(Name='sentinel-trail')
                event['remediation_status'] = 'SUCCESS'
                print("REMEDIATED: Re-enabled CloudTrail logging")
            except Exception as e:
                event['remediation_status'] = 'FAILED: ' + str(e)
                print("REMEDIATION FAILED: " + str(e))
        else:
            event['remediation_status'] = 'N/A'

    # EVERYTHING ELSE — no auto-remediation
    else:
        event['remediation_status'] = 'N/A'

    return event
