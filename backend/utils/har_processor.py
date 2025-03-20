import json
from typing import List, Dict, Any

def process_har_file(content: bytes) -> List[Dict[str, Any]]:
    """
    Process a HAR file to extract API requests.
    
    Args:
        content (bytes): Raw content of the HAR file
        
    Returns:
        List[Dict[str, Any]]: List of extracted API requests
    """
    # Parse the HAR JSON
    har_data = json.loads(content.decode('utf-8'))
    
    # Extract entries from the HAR file
    entries = har_data.get('log', {}).get('entries', [])
    
    # Filter API requests (non-HTML responses)
    api_requests = []
    
    for entry in entries:
        request = entry.get('request', {})
        response = entry.get('response', {})
        
        # Get content type from response headers
        content_type = None
        for header in response.get('headers', []):
            if header.get('name', '').lower() == 'content-type':
                content_type = header.get('value', '')
                break
        
        # Skip requests with no content type
        if not content_type:
            continue
            
        # Always include endpoints that look like APIs
        url = request.get('url', '')
        is_api_endpoint = (
            '/api/' in url or 
            'api.' in url or
            '/graphql' in url or
            '/v1/' in url or 
            '/v2/' in url or
            '/rest/' in url or
            '.json' in url
        )
            
        # Skip HTML responses as specified in requirements (unless it has API in path)
        if 'text/html' in content_type.lower() and not is_api_endpoint:
            continue
        
        # Skip common static asset types (unless it has API in path)
        if not is_api_endpoint and any(asset_type in content_type.lower() for asset_type in [
            'image/', 'font/', 'text/css'
        ]):
            continue
            
        # Calculate an API relevance score to better classify requests
        relevance_score = 0
        
        # Check if it's a potential data API
        is_json = 'json' in content_type.lower()
        is_javascript = 'javascript' in content_type.lower() or url.endswith('.js')
        is_data = 'application/octet-stream' in content_type.lower()
        is_xhr = request.get('method', '') != 'GET' or is_json or is_data or is_api_endpoint
        
        # Increase score for actual API endpoints
        if '/api/' in url or '.api.' in url:
            relevance_score += 10
        if '/data/' in url or '/common/' in url:
            relevance_score += 8
            
        # Increase score for JSON responses
        if is_json:
            relevance_score += 5
        
        # Decrease score for JavaScript files
        if is_javascript:
            relevance_score -= 5
            
        # Increase score for non-GET methods (POST, PUT, etc.)
        if request.get('method', '') != 'GET':
            relevance_score += 3
            
        # Include the request if it seems relevant
        if is_xhr:
            # Basic structure for each API request
            api_request = {
                'method': request.get('method'),
                'url': request.get('url'),
                'headers': {header['name']: header['value'] for header in request.get('headers', [])},
                'query_params': {param['name']: param['value'] for param in request.get('queryString', [])},
                'response_status': response.get('status'),
                'response_content_type': content_type,
                'relevance_score': relevance_score  # Add the calculated score
            }
            
            # Extract request body if present with enhanced information
            if 'postData' in request:
                post_data = request['postData']
                api_request['body'] = {
                    'mime_type': post_data.get('mimeType', ''),
                    'text': post_data.get('text', ''),
                    'params': []
                }
                
                # Add parameter parsing for form data
                if 'params' in post_data:
                    api_request['body']['params'] = [
                        {'name': param.get('name', ''), 'value': param.get('value', '')} 
                        for param in post_data.get('params', [])
                    ]
                    
                # Add context about the structure of the data
                if 'application/json' in post_data.get('mimeType', '').lower():
                    try:
                        api_request['body']['parsed_json'] = json.loads(post_data.get('text', '{}'))
                        api_request['body']['format'] = 'json'
                    except:
                        api_request['body']['format'] = 'text'
                elif 'form' in post_data.get('mimeType', '').lower():
                    api_request['body']['format'] = 'form'
                else:
                    api_request['body']['format'] = 'text'
            
            # Extract response body if present (truncated for large responses)
            if 'content' in response and 'text' in response['content']:
                response_text = response['content'].get('text', '')
                # Truncate large responses to reduce token usage, but preserve at least 2000 chars
                if len(response_text) > 2000:
                    response_text = response_text[:2000] + "... [truncated]"
                api_request['response_body'] = response_text
                
                # Try to parse response as JSON for better context
                if 'application/json' in content_type.lower():
                    try:
                        api_request['response_parsed'] = json.loads(response_text)
                    except:
                        pass
            
            api_requests.append(api_request)
    
    return api_requests