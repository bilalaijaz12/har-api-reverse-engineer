from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# Import the session storage from storage module
from utils.storage import session_storage

# Import LLM utilities
from utils.llm_service import identify_api_request
from utils.curl_generator import generate_curl_command
from utils.api_info import extract_api_info

router = APIRouter(
    prefix="/api",
    tags=["analyze"],
)

class AnalyzeRequest(BaseModel):
    session_id: str
    description: str

@router.post("/analyze")
async def analyze_api(request: AnalyzeRequest):
    """
    Analyze a HAR file to find the API request matching the description.
    
    Returns a curl command for the identified API request.
    """
    # Check if session exists
    if request.session_id not in session_storage:
        raise HTTPException(status_code=404, detail="Session not found. Please upload a HAR file first.")
    
    # Get the processed HAR data for this session
    processed_har = session_storage[request.session_id]["processed_har"]
    
    # Log the count of potential API requests
    print(f"Found {len(processed_har)} potential API requests in session {request.session_id}")
    
    try:
        # Pre-filter JavaScript files if user is looking for flight tracking data
        if any(keyword in request.description.lower() for keyword in ['flight', 'track', 'playback', 'data', 'map']):
            # Move JavaScript files to the end of the list
            sorted_requests = sorted(
                processed_har,
                key=lambda req: (
                    # Prioritize based on multiple factors:
                    # 1. Is it a JavaScript file? (penalize)
                    1 if req.get('url', '').endswith('.js') or 'javascript' in req.get('response_content_type', '').lower() else 0,
                    # 2. Is it a data API? (prioritize)
                    0 if '/api/' in req.get('url', '') or '/data/' in req.get('url', '') or '/common/' in req.get('url', '') else 1,
                    # 3. Does it return JSON? (prioritize)
                    0 if 'json' in req.get('response_content_type', '').lower() else 1,
                    # 4. Use the relevance score if available
                    -1 * req.get('relevance_score', 0)
                )
            )
            # Use these sorted requests for the API identification
            processed_har = sorted_requests
        
        # Use LLM to identify the most relevant API request
        api_request = identify_api_request(processed_har, request.description)
        
        # Additional validation for flight data APIs
        if 'flight' in request.description.lower() or 'track' in request.description.lower():
            # Check if the identified API is a JavaScript file when user is looking for data
            if api_request.get('url', '').endswith('.js') or 'javascript' in api_request.get('response_content_type', '').lower():
                # Try to find a better match
                for req in processed_har:
                    # Look for actual flight data API endpoints
                    if ('/api/' in req.get('url', '') and 'flight' in req.get('url', '').lower() and 
                        not req.get('url', '').endswith('.js')):
                        api_request = req
                        break
        
        # Validate identified API request to catch common errors
        validation_warnings = []
        
        # Check for potential ID mismatches in the body
        if 'body' in api_request and isinstance(api_request.get('body', {}).get('text', ''), str):
            body_text = api_request['body']['text']
            # Check if the body contains only numeric IDs that might be extracted from elsewhere
            if body_text.strip().isdigit():
                # Cross-reference this ID against request URLs to validate
                id_in_question = body_text.strip()
                image_urls = [req['url'] for req in processed_har if 'image' in req.get('response_content_type', '')]
                if any(id_in_question in url for url in image_urls):
                    # Check if this ID appears in other requests to this endpoint
                    endpoint_requests = [req for req in processed_har if req['url'] == api_request['url']]
                    if not any(id_in_question in req.get('body', {}).get('text', '') for req in endpoint_requests if req != api_request):
                        validation_warnings.append(f"The ID '{id_in_question}' may have been incorrectly extracted from image URLs rather than actual request data")
        
        # Important: Make sure we're working with the exact, original request
        # Find the original, complete request from the processed_har list
        original_request = None
        for req in processed_har:
            if (req.get('url') == api_request.get('url') and 
                req.get('method') == api_request.get('method')):
                original_request = req
                break
        
        # Use the original request if found, otherwise use the one returned by the LLM
        if original_request:
            api_request = original_request
            
        # Generate curl command from the identified API request
        curl_command = generate_curl_command(api_request)
        
        # Extract additional API information
        api_info = extract_api_info(api_request)
        
        # Add any validation warnings to the response
        if validation_warnings:
            api_info["validation_warnings"] = validation_warnings
        
        return {
            "curl_command": curl_command,
            "api_request": api_request,
            "api_info": api_info,
            "message": "API request identified successfully",
            "total_api_count": len(processed_har)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing API requests: {str(e)}")