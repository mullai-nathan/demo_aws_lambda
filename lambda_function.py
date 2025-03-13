import os
import re
import json
import base64


def lambda_handler(event, context):
    # Retrieve the "proxy" parameter from the event (if available)
    proxy_path = None
    if "pathParameters" in event and event["pathParameters"]:
        proxy_path = event["pathParameters"].get("proxy")
    
    # Use the proxy value if provided; otherwise, default to "/"
    path = proxy_path if proxy_path is not None else "/"
    
    # Normalize the path: collapse multiple slashes and remove any leading slash
    normalized_path = re.sub(r'//+', '/', path)
    if normalized_path.startswith('/'):
        normalized_path = normalized_path[1:]
    
    # Convert the normalized path to lowercase for a case-insensitive lookup
    lower_path = normalized_path.lower()
    
    # If no path is provided (empty), default to "index.html"
    if lower_path == "":
        lower_path = "index.html"
    
    # Allow access only if the path is "index.html" or starts with "downloads"
    if lower_path != "index.html" and not lower_path.startswith("downloads"):
        return {
            "statusCode": 403,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Access denied."})
        }
    
    # Construct the absolute file path using BASE_DIR and the lower-case path
    file_path = lower_path
    file_path = os.path.join(os.getcwd(), file_path)

    
    # Determine content type and headers based on file extension
    if file_path.lower().endswith(".xml"):
        content_type = "text/xml"  # or "application/rss+xml"
        headers = {"Content-Type": content_type}
    elif file_path.lower().endswith(".exe"):
        content_type = "application/octet-stream"
        headers = {
            "Content-Type": content_type,
            "Content-Disposition": f"attachment; filename={os.path.basename(file_path)}"
        }
    elif file_path.lower().endswith(".html"):
        content_type = "text/html"
        headers = {"Content-Type": content_type}
    else:
        return {
            "statusCode": 403,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Access denied. Only XML, EXE, or HTML files are allowed."})
        }
    
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # For XML and HTML files, return as plain text; for EXE, return as base64 encoded string.
        if file_path.lower().endswith((".xml", ".html")):
            body = file_data.decode("utf-8")
            is_base64 = False
        else:
            body = base64.b64encode(file_data).decode("utf-8")
            is_base64 = True
        
        return {
            "statusCode": 200,
            "headers": headers,
            "isBase64Encoded": is_base64,
            "body": body
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "file_path": file_path,
                "error": f"Error reading file: {str(e)}"
            })
        }
