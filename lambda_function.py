import base64
import os
import re

# Define the base directory for your static files
BASE_DIR = os.path.join(os.getcwd(), "downloads", "autoupdate", "app", "client")

def lambda_handler(event, context):
    # Retrieve the full request path from API Gateway
    path = event.get("path", "/")
    
    # Normalize path (collapse multiple slashes) and remove leading slash
    normalized_path = re.sub(r'//+', '/', path)
    if normalized_path.startswith('/'):
        normalized_path = normalized_path[1:]
    
    # Construct the absolute file path
    file_path = os.path.join(BASE_DIR, normalized_path)
    
    # If file doesn't exist, return 404
    if not os.path.isfile(file_path):
        return {
            "statusCode": 404,
            "body": "File not found"
        }
    
    # Determine the content type based on the file extension
    if file_path.("appcast.xml"):
        content_type = "application/rss+xml"
        filename = "appcast.xml"
    elif file_path.endswith(".exe"):
        content_type = "application/octet-stream"
        filename = os.path.basename(file_path)
    else:
        content_type = "application/octet-stream"
        filename = os.path.basename(file_path)
    
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": content_type,
                "Content-Disposition": f"attachment; filename={filename}"
            },
            "isBase64Encoded": True,
            "body": base64.b64encode(file_data).decode("utf-8")
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Error reading file: {str(e)}"
        }
