from typing import Dict, Any
import shlex
import json

def generate_curl_command(api_request: Dict[str, Any]) -> str:
    """
    Generate a curl command from an API request.
    
    Args:
        api_request: API request extracted from HAR
        
    Returns:
        String with the curl command
    """
    # Start with the basic curl command
    curl_cmd = ["curl"]
    
    # Add method if not GET
    if api_request.get('method', 'GET') != 'GET':
        curl_cmd.extend(["-X", api_request.get('method', 'GET')])
    
    # Add headers
    for name, value in api_request.get('headers', {}).items():
        # Skip HTTP/2 pseudo-headers and other unnecessary headers
        if name.lower() in ['connection', 'content-length', 'host'] or name.startswith(':'):
            continue
            
        # Skip compression-related headers to prevent decoding issues
        if name.lower() == 'accept-encoding':
            continue
            
        # Escape quotes in header values
        escaped_value = value.replace('"', '\\"')
        curl_cmd.extend(["-H", f'"{name}: {escaped_value}"'])
    
    # Add request body if present with proper format handling
    if 'body' in api_request and api_request.get('body', {}).get('text'):
        body_text = api_request.get('body', {}).get('text', '')
        mime_type = api_request.get('body', {}).get('mime_type', '')
        body_format = api_request.get('body', {}).get('format', 'text')
        
        # Format the body according to content type and format
        if 'json' in mime_type.lower() or body_format == 'json':
            try:
                # Try to parse and format JSON properly
                json_body = json.loads(body_text)
                escaped_body = json.dumps(json_body).replace('"', '\\"')
                curl_cmd.extend(["-d", f'"{escaped_body}"'])
            except json.JSONDecodeError:
                # Fallback for invalid JSON
                escaped_body = body_text.replace('"', '\\"')
                curl_cmd.extend(["-d", f'"{escaped_body}"'])
        elif 'form' in mime_type.lower() or body_format == 'form':
            # Handle form data with proper formatting
            if 'params' in api_request.get('body', {}) and api_request['body']['params']:
                params = api_request['body']['params']
                form_data = '&'.join([f"{p['name']}={p['value']}" for p in params])
                escaped_body = form_data.replace('"', '\\"')
                curl_cmd.extend(["-d", f'"{escaped_body}"'])
            else:
                # Fallback to raw text if no params are found
                escaped_body = body_text.replace('"', '\\"')
                curl_cmd.extend(["-d", f'"{escaped_body}"'])
        else:
            # Plain text or other formats
            escaped_body = body_text.replace('"', '\\"')
            curl_cmd.extend(["-d", f'"{escaped_body}"'])
    
    # Add the URL at the end
    url = api_request.get('url', '')
    curl_cmd.append(f'"{url}"')
    
    # Join all parts of the command
    return " ".join(curl_cmd)