import os
import json
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def optimize_for_tokens(api_requests: List[Dict[str, Any]], max_tokens: int = 12000) -> List[Dict[str, Any]]:
    """
    Optimize API requests to fit within token limits while preserving complete JSON.
    Also performs pre-filtering to prioritize data API endpoints.
    
    Args:
        api_requests: List of API requests extracted from HAR
        max_tokens: Maximum number of tokens to use
        
    Returns:
        List of optimized API requests
    """
    # Pre-filtering to prioritize data APIs and de-prioritize static resources
    filtered_requests = []
    
    # First, collect all requests that are likely to be data APIs
    data_api_requests = []
    possible_api_requests = []
    static_resource_requests = []
    
    for request in api_requests:
        url = request.get('url', '').lower()
        content_type = request.get('response_content_type', '').lower()
        
        # Check if it's a JavaScript file or other static resource
        if url.endswith('.js') or 'javascript' in content_type:
            static_resource_requests.append(request)
            continue
            
        # Check if it's an actual API endpoint
        if (('/api/' in url or '.api.' in url or '/common/' in url or '/data/' in url) and 
            ('json' in content_type or 'application/json' in content_type)):
            data_api_requests.append(request)
            continue
            
        # Other possible API endpoints
        if 'json' in content_type or 'application/json' in content_type:
            possible_api_requests.append(request)
            continue
            
        # Everything else
        static_resource_requests.append(request)
    
    # Combine the lists with priorities
    filtered_requests = data_api_requests + possible_api_requests + static_resource_requests
    
    # Proceed with token optimization on the prioritized list
    optimized_requests = []
    
    for request in filtered_requests:
        # Create a simplified version of the request
        optimized_request = {
            'method': request.get('method'),
            'url': request.get('url'),
            'response_status': request.get('response_status'),
            'response_content_type': request.get('response_content_type')
        }
        
        # Include only important headers
        important_headers = ['content-type', 'authorization', 'accept', 'user-agent', 'origin', 'referer']
        optimized_request['headers'] = {
            k: v for k, v in request.get('headers', {}).items()
            if k.lower() in important_headers
        }
        
        # Include query parameters
        if 'query_params' in request and request['query_params']:
            optimized_request['query_params'] = request['query_params']
        
        # Include body if present, preserving complete JSON structure
        if 'body' in request:
            body_text = request.get('body', {}).get('text', '')
            mime_type = request.get('body', {}).get('mime_type', '')
            body_format = request.get('body', {}).get('format', 'text')
            
            optimized_request['body'] = {
                'mime_type': mime_type,
                'format': body_format,
                'text': body_text
            }
            
            # Include parsed JSON if available
            if 'parsed_json' in request.get('body', {}):
                optimized_request['body']['parsed_json'] = request['body']['parsed_json']
                
            # Include form params if available
            if 'params' in request.get('body', {}) and request['body']['params']:
                optimized_request['body']['params'] = request['body']['params']
        
        # Include response body if present (summarized for non-JSON responses)
        if 'response_body' in request:
            response_body = request.get('response_body', '')
            content_type = request.get('response_content_type', '')
            
            if 'json' in content_type.lower() and len(response_body) > 500:
                try:
                    # Parse JSON to make sure we don't truncate in the middle of a JSON structure
                    json_obj = json.loads(response_body)
                    # Convert back to string without indentation to save tokens
                    response_body = json.dumps(json_obj)
                except json.JSONDecodeError:
                    # If parsing fails, just truncate safely
                    if len(response_body) > 500:
                        response_body = response_body[:500] + "... [truncated]"
            elif len(response_body) > 500:
                response_body = response_body[:500] + "... [truncated]"
                
            optimized_request['response_body'] = response_body
            
            # Include parsed response if available
            if 'response_parsed' in request:
                optimized_request['response_parsed'] = request['response_parsed']
        
        optimized_requests.append(optimized_request)
    
    return optimized_requests

def identify_api_request(api_requests: List[Dict[str, Any]], description: str) -> Dict[str, Any]:
    """
    Use OpenAI API to identify the API request that matches the description.
    
    Args:
        api_requests: List of API requests extracted from HAR
        description: User's description of the API they want to find
        
    Returns:
        The matched API request
    """
    # Optimize requests for token usage
    optimized_requests = optimize_for_tokens(api_requests)
    
    # Construct the prompt
    system_prompt = """You are an expert at identifying DATA API requests from HAR files.
    You will be provided with a list of API requests and a description of what the user is looking for.
    
    Analyze each API request carefully, including:
    1. The URL pattern and how it maps to the user's description
    2. The HTTP method and its appropriateness for the described operation
    3. The request headers and their significance
    4. The EXACT request body format, noting whether it's JSON, form data, or plain text
    5. The correlation between request parameters and the description
    6. The content type of the response (prioritize JSON/data responses over JavaScript files)
    
    IMPORTANT GUIDELINES:
    - PRIORITIZE actual DATA API endpoints that return JSON or structured data over JavaScript files, CSS, or other static resources
    - Look for endpoints that contain "api", "data", "common", or other indicators of actual data services
    - Specifically ignore JavaScript files (.js) unless the user is explicitly asking for a JavaScript resource
    - Specifically prioritize endpoints that return application/json content type
    - Pay close attention to the EXACT format of request bodies
    - Do not extract IDs from image URLs or other sources - only use IDs that appear in actual API requests
    - Distinguish between related APIs that might have similar purposes
    - If you see numeric IDs in the request, verify they are part of the actual request payload, not just referenced elsewhere
    - If multiple API endpoints could match the description, choose the one that most directly fulfills the user's needs
    - If the user is looking for data about flights, maps, tracking, etc., prioritize actual DATA APIs over analytics or advertising scripts
    
    Return ONLY the JSON of the most relevant API request with no additional text or explanations.
    DO NOT modify the structure or content of the selected request in any way.
    """
    
    user_prompt = f"""Description: {description}
    
    API Requests:
    {json.dumps(optimized_requests, indent=2)}
    
    Return ONLY the most relevant DATA API request as a JSON object, exactly as it appears in the list above.
    DO NOT modify the structure or content of the selected request in any way.
    When looking for flight or tracking data, prioritize API endpoints returning JSON data over JavaScript files.
    """
    
    # Call the OpenAI API
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-2024-08-06",  # Using the model specified in requirements
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1  # Low temperature for more deterministic output
        )
        
        # Extract the response content
        response_content = response.choices[0].message.content.strip()
        
        try:
            # Parse the JSON response
            matched_request = json.loads(response_content)
            return matched_request
        except json.JSONDecodeError:
            # If the response isn't valid JSON, look for a JSON object in the text
            import re
            match = re.search(r'({.*})', response_content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # If we still can't parse JSON, return the first API request as a fallback
            if optimized_requests:
                return optimized_requests[0]
            else:
                raise ValueError("No API requests found in the HAR file")
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        # Fall back to the first request if there's an API error
        if optimized_requests:
            return optimized_requests[0]
        else:
            raise ValueError("No API requests found in the HAR file")