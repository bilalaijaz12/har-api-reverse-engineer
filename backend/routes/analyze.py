from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# Import the session storage from storage module
from utils.storage import session_storage

# Import LLM utilities
from utils.llm_service import identify_api_request_with_confidence, verify_har_relevance
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
        # First, verify if the user's query is relevant to the HAR content
        is_relevant = verify_har_relevance(processed_har, request.description)
        
        if not is_relevant:
            return {
                "message": "The HAR file does not appear to contain APIs related to your query.",
                "curl_command": None,
                "api_info": {
                    "description": "No relevant API found. This HAR file does not appear to contain data for your query.",
                    "parameters": [],
                    "authentication": {"type": "unknown", "location": "unknown", "key": "unknown"},
                    "usage_notes": "The APIs in this HAR file do not match your description.",
                    "response_format": "Unknown response format",
                    "confidence": 0.0  # Explicitly set to zero
                },
                "total_api_count": len(processed_har)
            }
        
        # Use LLM to identify the most relevant API request with confidence score
        api_request, confidence = identify_api_request_with_confidence(processed_har, request.description)
        
        # Generate curl command only if confidence is adequate
        # Lower the threshold to make sure we're getting proper scores
        curl_command = generate_curl_command(api_request) if confidence >= 0.1 else None
        
        # Extract additional API information
        api_info = extract_api_info(api_request)
        
        # Make sure the confidence from LLM is preserved exactly
        api_info["confidence"] = confidence
        
        # Add warning message for low confidence
        if confidence < 0.4:
            api_info["warning"] = "Low confidence match. The requested data may not be available in this HAR file."
        
        return {
            "curl_command": curl_command,
            "api_request": api_request if confidence >= 0.1 else None,
            "api_info": api_info,
            "message": "API request identified successfully" if confidence >= 0.4 else 
                      "Low confidence match - API may not be relevant",
            "total_api_count": len(processed_har)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing API requests: {str(e)}")