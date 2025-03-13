import json
import base64
import boto3
import re
from botocore.exceptions import ClientError

s3 = boto3.client("s3")

BUCKET_NAME = "otaupdatebucket"

# 🔹 MIME Types Mapping
CONTENT_TYPES = {
    ".xml": "text/xml",
    ".html": "text/html",
    ".zip": "application/zip",
    ".exe": "application/octet-stream"
}

# Function to check if a file exists in S3
def check_file_exists(bucket_name, file_key):
    try:
        s3.head_object(Bucket=bucket_name, Key=file_key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise e  # Rethrow unexpected errors

# Function to create a response
def create_response(status_code, body, headers=None, is_base64=False):
    response = {
        "statusCode": status_code,
        "headers": headers if headers else {"Content-Type": "application/json"},
        "body": base64.b64encode(body).decode("utf-8") if is_base64 else body,
        "isBase64Encoded": is_base64
    }
    return response

# Function to fetch the file from S3
def fetch_file_from_s3(bucket_name, file_key):
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        return response["Body"].read()
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return None  # File does not exist
        raise e  # Rethrow other S3 errors

# Handle XML & HTML Files (Text-Based)
def handle_text_file(file_data, file_key):
    headers = {"Content-Type": CONTENT_TYPES.get(file_key[-4:], "text/plain")}
    return create_response(200, file_data.decode("utf-8"), headers)

# Handle ZIP & EXE Files (Binary)
def handle_binary_file(file_data, file_key):
    headers = {
        "Content-Type": CONTENT_TYPES[file_key[-4:]],
        "Content-Disposition": f"attachment; filename={file_key}"
    }
    return create_response(200, file_data, headers, is_base64=True)

# Main Lambda Handler
def lambda_handler(event, context):
    try:
        # Extract file path
        if "pathParameters" in event and event["pathParameters"]:
            proxy_path = event["pathParameters"].get("proxy")

        path = proxy_path if proxy_path is not None else "/"

        normalized_path = re.sub(r'//+', '/', path)
        if normalized_path.startswith('/'):
            normalized_path = normalized_path[1:]

        file_key = normalized_path

        if file_key == "":
            file_key = "index.html"
            return handle_text_file(file_data, file_key)


        if not file_key:
            return create_response(400, json.dumps({"error": "Invalid file request"}))

        # Validate file type
        if not re.search(r"\.(xml|html|zip|exe)$", file_key, re.IGNORECASE):
            return create_response(403, json.dumps({"error": "Access denied. Unsupported file type."}))

        
        # Check if file exists in S3
        if not check_file_exists(BUCKET_NAME, file_key):
            return create_response(404, json.dumps({"error": "File not found"}))

        # Fetch file from S3
        file_data = fetch_file_from_s3(BUCKET_NAME, file_key)
        if file_data is None:
            return create_response(404, json.dumps({"error": "File not found"}))

        # Determine file handling based on extension
        if file_key.endswith((".xml", ".html")):
            return handle_text_file(file_data, file_key)
        elif file_key.endswith((".zip", ".exe")):
            return handle_binary_file(file_data, file_key)

        return create_response(400, json.dumps({"error": "Access denied"}))

    except ClientError as e:
        return create_response(500, json.dumps({"error": f"S3 Error: {str(e)}"}))

    except Exception as e:
        return create_response(500, json.dumps({"error": f"Unexpected error: {str(e)}"}))
