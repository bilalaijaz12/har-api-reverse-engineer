from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import subprocess
import shlex
import json
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter(
    prefix="/api",
    tags=["test"],
)

class TestRequest(BaseModel):
    curl_command: str

class InterpretRequest(BaseModel):
    api_response: str
    api_description: str

@router.post("/test")
async def test_api(request: TestRequest):
    """
    Execute a curl command and return the response.
    """
    try:
        # Clean up the curl command - remove line continuations and normalize spaces
        clean_cmd = request.curl_command.replace("\\\n", " ").strip()
        
        # Log the command being executed
        print(f"Executing cleaned curl command: {clean_cmd}")
        
        # Execute the curl command directly with shell=True to handle complex commands
        # Note: shell=True should be used carefully in production environments
        result = subprocess.run(clean_cmd, shell=True, capture_output=True, text=True)
        
        # Check if the command was successful
        if result.returncode != 0:
            error_detail = f"Return code: {result.returncode}, Stderr: {result.stderr}"
            print(f"Curl command failed: {error_detail}")
            return {
                "status_code": 500,
                "headers": {},
                "response": f"Curl command failed: {error_detail}"
            }
        
        # Try to parse the response as JSON
        try:
            json_response = json.loads(result.stdout)
            response_text = json.dumps(json_response, indent=2)
        except json.JSONDecodeError:
            # If not JSON, return as plain text
            response_text = result.stdout
        
        # Attempt to determine status code (this is approximate since we're using subprocess)
        status_code = 200  # Default to 200 if successful
        
        return {
            "status_code": status_code,
            "headers": {},  # We don't have header info when using subprocess
            "response": response_text
        }
    
    except Exception as e:
        error_detail = str(e)
        print(f"Error executing API request: {error_detail}")
        return {
            "status_code": 500,
            "headers": {},
            "response": f"Error executing API request: {error_detail}"
        }
    
@router.post("/interpret")
async def interpret_response(request: InterpretRequest):
    """
    Use OpenAI to interpret the API response in natural language.
    """
    try:
        # Construct the prompt
        system_prompt = """You are an API expert who explains API responses in plain language.
        Your task is to analyze an API response and explain what information it contains and what it means.
        Provide a concise summary followed by detailed explanations of the key data points.
        Format your response using Markdown for readability.
        """
        
        user_prompt = f"""API Description: {request.api_description}
        
        API Response:
        ```
        {request.api_response}
        ```
        
        Please interpret this API response in natural language. Explain what data it contains and what it means.
        """
        
        # Call the OpenAI API
        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            
            response = openai.chat.completions.create(
                model="gpt-4o-2024-08-06",  # Using the model specified in requirements
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5
            )
            
            # Extract the interpretation
            interpretation = response.choices[0].message.content
            
            return {
                "interpretation": interpretation
            }
        except ImportError:
            # If OpenAI isn't available, provide a fallback response
            return {
                "interpretation": "API response interpretation is not available. Please check the raw response."
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interpreting API response: {str(e)}")