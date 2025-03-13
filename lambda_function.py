import json
import base64
import boto3

s3 = boto3.client("s3")

BUCKET_NAME = "otaupdatebucket"

def lambda_handler(event, context):
    try:
        file_key = event.get("pathParameters", {}).get("proxy", "appcast.xml")

        print(f"Fetching file: {file_key}")  # Debug log

        if not file_key.endswith((".xml", ".exe")):
            print("Access Denied - Invalid File Type")  # Debug log
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Access denied."})
            }

        # Fetch file from S3
        response = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
        file_data = response["Body"].read()

        # Determine content type
        content_types = {
            ".xml": "text/xml",
            ".exe": "application/octet-stream"
        }
        content_type = content_types.get(file_key[-4:], "application/octet-stream")

        headers = {"Content-Type": content_type}

        # If it's an EXE, enable Base64 encoding
        is_base64 = False
        if file_key.endswith(".exe"):
            headers["Content-Disposition"] = f"attachment; filename={file_key}"
            is_base64 = True

        print("File successfully fetched!")  # Debug log

        return {
            "statusCode": 200,
            "headers": headers,
            "isBase64Encoded": is_base64,
            "file_key": file_key,
        }

    except Exception as e:
        print(f"Error: {str(e)}")  # Debug log
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Unexpected error: {str(e)}"})
        }
