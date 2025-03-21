import os
import json
from typing import Dict, Any, List
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_api_info(api_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use OpenAI to extract useful information about the API.
    
    Args:
        api_request: API request extracted from HAR
        
    Returns:
        Enhanced API information
    """
    try:
        # Construct the prompt
        system_prompt = """You are an expert API analyst. You'll be given information about an API request.
        Your task is to analyze it and provide useful information about this API including:
        
        1. What parameters it accepts (both required and optional)
        2. What authentication method it uses (if any)
        3. A brief description of what this API does
        4. Any rate limiting or special usage notes you can detect
        5. The expected response format
        
        IMPORTANT CONSIDERATIONS:
        1. Use semantic understanding to determine the true purpose of the API, beyond just the URL pattern
        2. Be specific and precise - explain exactly what the API does and how to use it
        3. Pay close attention to the exact format and structure of request bodies
        4. Analyze the response data to better understand the API's purpose
        5. When describing parameters, distinguish between URL parameters, query parameters, and body parameters
        6. For numeric IDs, explain their context and meaning if evident from the request structure
        7. Consider the domain context (weather, flights, banking, etc.) when describing the purpose
        8. If the API appears to be for retrieving specifications/details, explain what kind of details
        9. Identify authentication methods by examining headers, tokens, and request patterns
        10. Determine required vs. optional parameters by analyzing examples and context
        
        Return your analysis as a JSON object with these keys:
        {
            "parameters": [{"name": "param1", "description": "what this param does", "required": true/false, "type": "string/number/etc", "location": "url/query/body"}],
            "authentication": {"type": "none/api_key/oauth/basic/etc", "location": "header/query/etc", "key": "name of auth header or param"},
            "description": "brief description of what this API does",
            "usage_notes": "any rate limiting or special usage information",
            "response_format": "description of expected response structure"
        }
        """
        
        # Create a simplified version of the request
        simplified_request = {
            "method": api_request.get("method"),
            "url": api_request.get("url"),
            "headers": api_request.get("headers", {}),
            "query_params": api_request.get("query_params", {}),
        }
        
        if "body" in api_request:
            body_info = {
                "mime_type": api_request.get("body", {}).get("mime_type", ""),
                "format": api_request.get("body", {}).get("format", ""),
                "text": api_request.get("body", {}).get("text", "")
            }
            
            # Include parsed JSON or form params if available
            if "parsed_json" in api_request.get("body", {}):
                body_info["parsed_json"] = api_request["body"]["parsed_json"]
            if "params" in api_request.get("body", {}) and api_request["body"]["params"]:
                body_info["params"] = api_request["body"]["params"]
                
            simplified_request["body"] = body_info
            
        if "response_body" in api_request:
            # Include a sample of the response
            response_body = api_request.get("response_body", "")
            if len(response_body) > 1000:
                response_body = response_body[:1000] + "... [truncated]"
            simplified_request["response_sample"] = response_body
            
            # Include parsed response if available
            if "response_parsed" in api_request:
                simplified_request["response_parsed"] = api_request["response_parsed"]
                
        # Include content type of response
        if "response_content_type" in api_request:
            simplified_request["response_content_type"] = api_request.get("response_content_type")
            
        user_prompt = f"""API Request: {json.dumps(simplified_request, indent=2)}

User Description: Looking for an API that provides detailed information related to this domain.

Provide an analysis of this API - explain what it does, required and optional parameters, authentication method, usage notes, and expected response format. Focus on giving an accurate semantic understanding of the API's purpose and functioning.
"""
        
        # Call the OpenAI API
        response = openai.chat.completions.create(
            model="gpt-4o-2024-08-06",
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
            api_info = json.loads(response_content)
            return api_info
        except json.JSONDecodeError:
            # If the response isn't valid JSON, extract JSON using regex
            import re
            match = re.search(r'({.*})', response_content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # Fallback to a basic structure
            return {
                "parameters": [],
                "authentication": {"type": "unknown", "location": "unknown", "key": "unknown"},
                "description": "No description available",
                "usage_notes": "No usage notes available",
                "response_format": "Unknown response format"
            }
            
    except Exception as e:
        print(f"Error extracting API info: {str(e)}")
        return {
            "parameters": [],
            "authentication": {"type": "unknown", "location": "unknown", "key": "unknown"},
            "description": "Error extracting API information",
            "usage_notes": "No usage notes available",
            "response_format": "Unknown response format"
        }