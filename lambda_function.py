import json
import base64
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client("s3")

BUCKET_NAME = "otaupdatebucket"

def check_file_exists(bucket_name, file_key):
    """Check if a file exists in the S3 bucket."""
    try:
        s3.head_object(Bucket=bucket_name, Key=file_key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            return False
        raise e  # Rethrow unexpected errors

def create_response(status_code, message):
    """Generate a JSON response."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(message)
    }

def lambda_handler(event, context):
    try:
        proxy_path = None
        if "pathParameters" in event and event["pathParameters"]:
            proxy_path = event["pathParameters"].get("proxy")

        # Use the proxy value if provided; otherwise, default to "/"
        path = proxy_path if proxy_path is not None else "/"

        # Normalize the path: collapse multiple slashes and remove any leading slash
        normalized_path = re.sub(r'//+', '/', path)
        if normalized_path.startswith('/'):
            normalized_path = normalized_path[1:]

        file_key = normalized_path
        # Check if the file exists in S3
        if not check_file_exists(BUCKET_NAME, file_key):
            return create_response(404, {"error": "File not found"})

        return create_response(200, {"filename": base_filename})

    except ClientError as e:
        return create_response(500, {"error": f"S3 Error: {str(e)}"})

    except Exception as e:
        return create_response(500, {"error": f"Unexpected error: {str(e)}"})