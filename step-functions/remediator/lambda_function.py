import boto3


def lambda_handler(event, context):
    s3 = boto3.client('s3')
    cloudtrail = boto3.client('cloudtrail', region_name='us-east-2')
    category = event.get('category', '')
    bucket = event.get('bucket', '')
    event_name = event.get('eventName', '')

    # S3 PUBLIC ACCESS — verify live state, then remediate if actually public
    if category == 'S3_PUBLIC_ACCESS':
        is_public = False
        findings = []

        # Check 1: Public Access Block
        try:
            pab = s3.get_public_access_block(Bucket=bucket)
            block = pab['PublicAccessBlockConfiguration']
            if not block.get('BlockPublicAcls', False):
                is_public = True
                findings.append('BlockPublicAcls is disabled')
            if not block.get('IgnorePublicAcls', False):
                is_public = True
                findings.append('IgnorePublicAcls is disabled')
            if not block.get('BlockPublicPolicy', False):
                is_public = True
                findings.append('BlockPublicPolicy is disabled')
            if not block.get('RestrictPublicBuckets', False):
                is_public = True
                findings.append('RestrictPublicBuckets is disabled')
        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                is_public = True
                findings.append('No Public Access Block configured')
            else:
                print("Error checking Public Access Block: " + str(e))
        except Exception as e:
            print("Error checking Public Access Block: " + str(e))

        # Check 2: Bucket Policy public status
        try:
            policy_status = s3.get_bucket_policy_status(Bucket=bucket)
            if policy_status['PolicyStatus']['IsPublic']:
                is_public = True
                findings.append('Bucket policy allows public access')
        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                pass  # No policy = not public via policy
            else:
                print("Error checking Bucket Policy: " + str(e))
        except Exception as e:
            print("Error checking Bucket Policy: " + str(e))

        # Check 3: Bucket ACL grants
        try:
            acl = s3.get_bucket_acl(Bucket=bucket)
            for grant in acl.get('Grants', []):
                grantee = grant.get('Grantee', {})
                uri = grantee.get('URI', '')
                if 'AllUsers' in uri:
                    is_public = True
                    findings.append('ACL grants access to AllUsers (public)')
                if 'AuthenticatedUsers' in uri:
                    is_public = True
                    findings.append('ACL grants access to AuthenticatedUsers')
        except Exception as e:
            print("Error checking Bucket ACL: " + str(e))

        # Only remediate if bucket is actually public
        if is_public:
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
                event['findings'] = findings
                print("REMEDIATED: Blocked public access on " + bucket)
                print("Findings: " + str(findings))
            except Exception as e:
                event['remediation_status'] = 'FAILED: ' + str(e)
                event['findings'] = findings
                print("REMEDIATION FAILED: " + str(e))
        else:
            event['remediation_status'] = 'NOT_NEEDED'
            event['findings'] = []
            print("Bucket " + bucket + " is not currently public. No remediation needed.")

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
