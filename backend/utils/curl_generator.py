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
            # Skip HTTP/2 pseudo-headers and other unnecessary headers
            if name.lower() in ['content-length'] or name.startswith(':'):
                continue
                
            # Escape single quotes in header values
            escaped_value = value.replace("'", "'\\''")
            curl_cmd.append(f"  -H '{name}: {escaped_value}'")
    
    # Add method if not GET
    if api_request.get('method', 'GET') != 'GET':
        curl_cmd.insert(1, f"  -X {api_request.get('method', 'GET')}")
    
    # Add request body if present with proper format handling
    if 'body' in api_request and api_request.get('body', {}).get('text'):
        body_text = api_request.get('body', {}).get('text', '')
        mime_type = api_request.get('body', {}).get('mime_type', '')
        
        # Escape single quotes in body
        escaped_body = body_text.replace("'", "'\\''")
        curl_cmd.append(f"  -d '{escaped_body}'")
    
    # Join all parts of the command with line continuations for readability
    return " \\\n".join(curl_cmd)