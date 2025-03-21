import json
from typing import List, Dict, Any
import re

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
    
    # Filter API requests
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
            
        url = request.get('url', '')
        
        # Define patterns for different types of endpoints
        is_api_endpoint = (
            '/api/' in url or 
            'api.' in url or
            '/graphql' in url or
            '/v1/' in url or 
            '/v2/' in url or
            '/rest/' in url or
            '.json' in url
        )
        
        # Data resource pattern - /data/[entity-type]/[entity-id]
        # This pattern is common across many domains for entity data
        data_path_match = re.search(r'/data/[^/]+/[^/?&]+', url)
        is_data_resource = bool(data_path_match)
        
        # Entity resource pattern - /[entity-type]/[entity-id] 
        # This is also common for retrieving entity data
        entity_path_match = re.search(r'/[^/]+/[^/?&]+$', url)
        is_entity_resource = bool(entity_path_match) and not url.endswith(('.js', '.css', '.jpg', '.png', '.gif'))
            
        # Skip HTML responses unless it has API or data resource patterns
        # We want to include HTML pages that might contain entity data
        if 'text/html' in content_type.lower() and not (is_api_endpoint or is_data_resource or is_entity_resource):
            continue
        
        # Skip common static asset types
        if not (is_api_endpoint or is_data_resource or is_entity_resource) and any(asset_type in content_type.lower() for asset_type in [
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
        
        # Data resource pages should get high priority
        if is_data_resource:
            relevance_score += 15
            
        # Entity resource pages should get medium-high priority
        if is_entity_resource:
            relevance_score += 12
            
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
        if is_xhr or is_data_resource or is_entity_resource or '/data/' in url:
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
            
            # Extract request body if present
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
            
            # Extract response body if present
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
    
    # Sort requests by relevance score in descending order
    api_requests = sorted(api_requests, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    return api_requests