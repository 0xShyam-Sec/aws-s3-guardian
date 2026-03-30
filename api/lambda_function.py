import boto3
import json


def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('sentinel-findings')

    # Get query parameters
    params = event.get('queryStringParameters') or {}

    # Get path - try multiple fields that API Gateway might use
    path = event.get('path', '')
    resource = event.get('resource', '')

    # Check if path contains findings or stats
    is_findings = 'findings' in path or 'findings' in resource
    is_stats = 'stats' in path or 'stats' in resource

    # CORS headers - required for browser to call this API
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    try:
        if is_findings:
            response = table.scan()
            items = response.get('Items', [])

            severity = params.get('severity')
            if severity:
                items = [i for i in items if i.get('severity') == severity]

            category = params.get('category')
            if category:
                items = [i for i in items if i.get('category') == category]

            items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'count': len(items),
                    'findings': items
                })
            }

        elif is_stats:
            response = table.scan()
            items = response.get('Items', [])

            severity_counts = {}
            for item in items:
                sev = item.get('severity', 'UNKNOWN')
                severity_counts[sev] = severity_counts.get(sev, 0) + 1

            category_counts = {}
            for item in items:
                cat = item.get('category', 'UNKNOWN')
                category_counts[cat] = category_counts.get(cat, 0) + 1

            status_counts = {}
            for item in items:
                status = item.get('status', 'UNKNOWN')
                status_counts[status] = status_counts.get(status, 0) + 1

            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'totalFindings': len(items),
                    'bySeverity': severity_counts,
                    'byCategory': category_counts,
                    'byStatus': status_counts
                })
            }

        else:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'message': 'AWS S3 Guardian API',
                    'endpoints': [
                        'GET /findings - All findings',
                        'GET /findings?severity=HIGH - Filter by severity',
                        'GET /findings?category=IAM_CHANGE - Filter by category',
                        'GET /stats - Summary statistics'
                    ]
                })
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
