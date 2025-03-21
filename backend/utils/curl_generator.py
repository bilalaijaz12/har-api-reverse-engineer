from typing import Dict, Any
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
    url = api_request.get('url', '')
    curl_cmd = [f"curl '{url}'"]
    
    # Log the request structure to help debug
    print(f"API request structure: {list(api_request.keys())}")
    print(f"Headers present: {'headers' in api_request}")
    if 'headers' in api_request:
        print(f"Number of headers: {len(api_request['headers'])}")
    
    # Add all headers with proper formatting and line continuation
    if 'headers' in api_request and api_request['headers']:
        for name, value in api_request['headers'].items():
            # Skip certain headers that are automatically added by browsers/clients
            if name.lower() in ['content-length', 'host', 'connection', 'pragma', 'cache-control'] or name.startswith(':'):
                continue
                
            # Escape single quotes in header values
            escaped_value = value.replace("'", "'\\''")
            curl_cmd.append(f"  -H '{name}: {escaped_value}'")
    
    # Add method if not GET
    if api_request.get('method', 'GET') != 'GET':
        curl_cmd.insert(1, f"  -X {api_request.get('method', 'GET')}")
    
    # Add query parameters if they're not already in the URL
    if 'query_params' in api_request and api_request['query_params'] and '?' not in url:
        query_string = '&'.join([f"{k}={v}" for k, v in api_request['query_params'].items()])
        # Replace the URL in the first entry
        curl_cmd[0] = f"curl '{url}?{query_string}'"
    
    # Add request body if present with proper format handling
    if 'body' in api_request and api_request.get('body', {}).get('text'):
        body_text = api_request.get('body', {}).get('text', '')
        mime_type = api_request.get('body', {}).get('mime_type', '')
        
        # Escape single quotes in body
        escaped_body = body_text.replace("'", "'\\''")
        
        # Format the body parameter properly based on content type
        if 'json' in mime_type.lower():
            # For JSON, add proper content-type if not already in headers
            has_content_type = False
            for header in curl_cmd:
                if '-H' in header and 'content-type: application/json' in header.lower():
                    has_content_type = True
                    break
            
            if not has_content_type:
                curl_cmd.append(f"  -H 'Content-Type: application/json'")
                
            curl_cmd.append(f"  -d '{escaped_body}'")
        elif 'form' in mime_type.lower():
            # For form data, use --data-urlencode
            if 'params' in api_request.get('body', {}):
                for param in api_request['body']['params']:
                    param_name = param.get('name', '')
                    param_value = param.get('value', '')
                    curl_cmd.append(f"  --data-urlencode '{param_name}={param_value}'")
            else:
                curl_cmd.append(f"  --data-urlencode '{escaped_body}'")
        else:
            # Default for other content types
            curl_cmd.append(f"  -d '{escaped_body}'")
    
    # Join all parts of the command with line continuations for readability
    return " \\\n".join(curl_cmd)