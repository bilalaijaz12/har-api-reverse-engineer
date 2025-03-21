import os
import json
import openai
from dotenv import load_dotenv
from typing import List, Dict, Any, Tuple
import re

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
        method = request.get('method', '').upper()
        
        # Check if it's a JavaScript file or other static resource
        if url.endswith('.js') or 'javascript' in content_type:
            static_resource_requests.append(request)
            continue
            
        # Check if it has indicators of being a data API
        has_api_indicators = (
            '/api/' in url or 
            '.api.' in url or 
            '/v1/' in url or 
            '/v2/' in url or 
            '/data/' in url or
            '/common/' in url
        )
        
        is_data_response = (
            'json' in content_type or 
            'application/json' in content_type
        )
        
        # Non-GET methods are more likely to be important API calls
        is_action_method = method != 'GET'
            
        # Categorize based on likelihood of being a relevant API
        if has_api_indicators and is_data_response:
            data_api_requests.append(request)
        elif is_data_response or is_action_method or has_api_indicators:
            possible_api_requests.append(request)
        else:
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
        important_headers = ['content-type', 'authorization', 'accept', 'user-agent', 'origin', 'referer', 'x-api-key']
        optimized_request['headers'] = {
            k: v for k, v in request.get('headers', {}).items()
            if k.lower() in important_headers or 'auth' in k.lower() or 'token' in k.lower() or 'key' in k.lower()
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
        
        # Include response body if present (with smart truncation for JSON)
        if 'response_body' in request:
            response_body = request.get('response_body', '')
            content_type = request.get('response_content_type', '')
            
            # Use semantic truncation for JSON responses
            if 'json' in content_type.lower():
                try:
                    # Parse JSON to make sure we don't truncate in the middle of a JSON structure
                    json_obj = json.loads(response_body)
                    
                    # If this is a large array, keep only first few items
                    if isinstance(json_obj, list) and len(json_obj) > 3:
                        json_obj = json_obj[:3]
                        
                    # If this is a large object, keep only essential properties
                    if isinstance(json_obj, dict) and len(json_obj) > 10:
                        # Keep a subset of keys that are likely to be more important
                        # (metadata, status, first few data entries)
                        priority_keys = ['id', 'name', 'title', 'description', 'status', 'metadata', 'count', 'total']
                        truncated_obj = {}
                        
                        # First add priority keys if they exist
                        for key in priority_keys:
                            if key in json_obj:
                                truncated_obj[key] = json_obj[key]
                        
                        # Then add other keys up to a limit
                        other_keys = [k for k in json_obj.keys() if k not in truncated_obj]
                        for key in other_keys[:7]:  # Add up to 7 more keys
                            truncated_obj[key] = json_obj[key]
                            
                        json_obj = truncated_obj
                    
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

def verify_har_relevance(api_requests: List[Dict[str, Any]], description: str) -> bool:
    """
    Verify if the user's description is relevant to the content in the HAR file.
    
    Args:
        api_requests: List of API requests extracted from HAR
        description: User's description of the API they want to find
        
    Returns:
        Boolean indicating if the description is relevant to the HAR content
    """
    # If there are fewer than 5 APIs, just return True to avoid false negatives
    if len(api_requests) < 5:
        print(f"Few API requests ({len(api_requests)}), assuming relevance")
        return True
    
    # Get the top 20 most promising requests (or all if fewer than 20)
    sample_size = min(20, len(api_requests))
    
    # Include all API requests in sampling for maximum coverage
    sample_requests = api_requests[:sample_size]
    
    # Extract key information from sample requests
    sampled_info = []
    for req in sample_requests:
        # Create a representation with enough info to understand context
        req_info = {
            'method': req.get('method'),
            'url': req.get('url'),
            'content_type': req.get('response_content_type', ''),
            'query_params': list(req.get('query_params', {}).keys()) if req.get('query_params') else []
        }
        
        # Include response snippets for context
        if 'response_body' in req and req['response_body']:
            response_snippet = req['response_body'][:150] if len(req['response_body']) > 150 else req['response_body']
            req_info['response_snippet'] = response_snippet
            
        sampled_info.append(req_info)
    
    # Construct the prompt
    system_prompt = """You are an expert at analyzing API requests from HAR files.
    Your task is to determine if a user's query about an API is relevant to the content in the HAR file.
    
    EXTREMELY IMPORTANT: Be VERY LENIENT in your judgment. Unless you are 100% certain that the HAR file could not possibly contain any API related to the user's query, answer YES.
    
    Consider these guidelines:
    
    1. Even tenuous connections should be considered relevant.
    2. Don't be too literal - if a user asks for "weather in Berlin" but you only see weather APIs for other cities, still say YES.
    3. Domain similarities matter - if user asks for flight data and you see any travel-related API, say YES.
    4. Common API patterns don't always explicitly state their purpose in URLs - a weather API might be at /api/data.
    5. Consider response content - if response data might relate to the query domain, say YES.
    
    EXAMPLES OF WHEN TO SAY YES:
    - User asks about weather, and there are any location or data APIs, even if not explicitly for weather
    - User asks about news articles, and there are content delivery APIs
    - User asks about flight tracking, and there are any transportation or location-based APIs
    - User asks about a specific city's data, and the APIs contain any location-based services
    
    ONLY SAY NO IF:
    The HAR file contains exclusively APIs from a completely different domain (e.g., user asks about banking APIs but the HAR contains only video streaming APIs).
    
    Return ONLY "YES" in almost all cases, or "NO" only if you are absolutely certain the query is completely unrelated.
    """
    
    user_prompt = f"""Description: {description}
    
    Sample API Requests from HAR file:
    {json.dumps(sampled_info, indent=2)}
    
    Based on these sample API requests, could this HAR file possibly contain APIs related to the user's description?
    Be extremely lenient - unless you're 100% certain it's unrelated, say YES.
    Answer only YES or NO.
    """
    
    # Call the OpenAI API
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        
        # Extract the response
        response_content = response.choices[0].message.content.strip().upper()
        is_relevant = response_content == "YES"
        
        # Detailed debug logging
        print(f"Relevance check for '{description}': RESULT = {response_content}")
        print(f"Number of API requests analyzed: {len(sample_requests)}")
        print(f"Sample URLs analyzed: {[req.get('url', '') for req in sample_requests][:5]}")
        
        # If the result is NO, log more details to help diagnose
        if not is_relevant:
            print(f"ATTENTION: Relevance check returned NO. This might be a false negative.")
            print(f"Description: '{description}'")
            print(f"First 3 sampled URLs: {[req.get('url', '') for req in sample_requests][:3]}")
            
        return is_relevant
        
    except Exception as e:
        print(f"Error verifying HAR relevance: {str(e)}")
        # Default to True in case of API errors to avoid blocking users
        return True
    

def identify_api_request_with_confidence(api_requests: List[Dict[str, Any]], description: str) -> Tuple[Dict[str, Any], float]:
    """
    Identify the API request matching the description with a confidence score.
    
    Args:
        api_requests: List of API requests extracted from HAR
        description: User's description of the API they want to find
        
    Returns:
        Tuple of (matched API request, confidence score 0-1)
    """
    # Optimize requests for token usage
    optimized_requests = optimize_for_tokens(api_requests)
    
    # Construct the prompt
    system_prompt = """You are an expert at identifying DATA API requests from HAR files.
    You will be provided with a list of API requests and a description of what the user is looking for.
    
    CRITICAL SEMANTIC UNDERSTANDING:
    - Distinguish between different types of data: STATIC REFERENCE DATA vs DYNAMIC TRACKING DATA vs MEDIA CONTENT
    - When users ask for "specifications," "technical information," or "dimensions" they usually want STATIC REFERENCE DATA
    - When users ask for "current status," "monitoring," or "tracking" they usually want DYNAMIC TRACKING DATA
    - Consider whether the user is seeking properties/attributes of an entity or tracking its activities/state
    
    URL PATTERN CONSIDERATIONS:
    - URLs containing "/data/" followed by an entity identifier often provide reference information
    - Resource paths like "/[entity-type]/[entity-id]" frequently contain detailed information
    - Parameters like "id," "timestamp," or "date" may indicate the type of data being requested
    - Don't rule out HTML endpoints - they often contain embedded structured data and specifications
    
    CONTENT TYPE CONSIDERATIONS:
    - Don't assume only JSON endpoints contain valuable data - HTML responses often contain embedded structured data
    - Consider the HTTP method - GET requests to entity-specific URLs often retrieve reference information
    - Text/HTML responses from RELEVANT PATHS should be rated appropriately when specifications are requested
    
    ANALYSIS APPROACH:
    1. First understand the semantic intent of the user's request (reference data, real-time data, etc.)
    2. Look for paths that match this semantic intent
    3. Consider whether the content type and response structure would contain the data the user needs
    4. Examine parameters and URL patterns for entity identifiers that match the user's request
    
    After analyzing all candidates, select the single best matching API and provide a confidence score between 0 and 1:
    - 0.9-1.0: Perfect match, API definitely provides the requested data
    - 0.7-0.8: Good match, API likely contains the requested data
    - 0.4-0.6: Possible match, API might contain some requested data but not complete
    - 0.1-0.3: Poor match, API probably contains related but not requested data
    - 0.0-0.1: Wrong type of data entirely
    
    Return your response in this format:
    ```
    API_REQUEST_JSON
    
    CONFIDENCE_SCORE
    ```
    """
    
    user_prompt = f"""Description: {description}
    
    API Requests:
    {json.dumps(optimized_requests, indent=2)}
    
    Return the most relevant API request that matches the user's description, considering both the semantic intent and the likely data contained in each endpoint. Don't dismiss HTML pages if they might contain the requested information.
    """
    
    # Call the OpenAI API
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        
        # Extract the response content
        response_content = response.choices[0].message.content.strip()
        
        # Parse the JSON and confidence score
        # First, find the JSON part
        import re
        json_match = re.search(r'({.*})', response_content, re.DOTALL)
        
        # Then find the confidence score
        confidence_match = re.search(r'([0-9]\.[0-9]+)', response_content)
        
        if json_match:
            try:
                matched_request = json.loads(json_match.group(1))
                confidence = float(confidence_match.group(1)) if confidence_match else 0.5
                return matched_request, confidence
            except json.JSONDecodeError:
                pass
        
        # If we couldn't parse properly, fall back to the first request with low confidence
        if optimized_requests:
            return optimized_requests[0], 0.1
        else:
            raise ValueError("No API requests found in the HAR file")
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        # Fall back to the first request if there's an API error
        if optimized_requests:
            return optimized_requests[0], 0.1
        else:
            raise ValueError("No API requests found in the HAR file")