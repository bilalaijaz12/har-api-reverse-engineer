from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import subprocess
import json
import shlex
import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

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
        # Parse the curl command to extract URL and headers
        parts = shlex.split(request.curl_command)
        url = parts[-1].strip('"\'')
        
        # Extract method
        method = "GET"
        if "-X" in parts:
            method_index = parts.index("-X")
            if method_index + 1 < len(parts):
                method = parts[method_index + 1]
        
        # Extract headers
        headers = {}
        for i, part in enumerate(parts):
            if part == "-H" and i + 1 < len(parts):
                header = parts[i + 1].strip('"\'')
                if ":" in header:
                    key, value = header.split(":", 1)
                    key = key.strip()
                    
                    # Skip HTTP/2 pseudo-headers (they start with ":")
                    if key.startswith(":"):
                        continue
                        
                    # Skip empty header names
                    if not key:
                        continue
                    
                    # Skip compression-related headers to prevent decoding issues
                    if key.lower() == 'accept-encoding':
                        continue
                        
                    headers[key] = value.strip()
        
        # Extract data if present
        data = None
        if "-d" in parts:
            data_index = parts.index("-d")
            if data_index + 1 < len(parts):
                data = parts[data_index + 1].strip('"\'')
        
        # Make the request
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, data=data)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, data=data)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported HTTP method: {method}")
        
        # Get content type for proper handling
        content_type = response.headers.get('content-type', '').lower()
        
        # Handle different content types appropriately
        if 'application/json' in content_type:
            try:
                # Try to parse JSON response
                json_response = json.loads(response.text)
                response_data = json.dumps(json_response, indent=2)
            except json.JSONDecodeError:
                # If not valid JSON, use the raw text
                response_data = response.text
        elif 'text/' in content_type:
            # Plain text response
            response_data = response.text
        else:
            # Binary data or other content types
            try:
                # Try to decode as UTF-8 first
                response_data = response.text
                # Check if the response is readable text
                if not is_readable_text(response_data):
                    # If not readable, provide a summary of binary content
                    content_length = len(response.content)
                    response_data = f"Binary data ({content_length} bytes, {content_type})\n"
                    # Add a hexdump preview for the first 200 bytes
                    response_data += hexdump(response.content[:200])
                    if content_length > 200:
                        response_data += "\n... (truncated)"
            except UnicodeDecodeError:
                # If can't decode as text, it's definitely binary
                content_length = len(response.content)
                response_data = f"Binary data ({content_length} bytes, {content_type})\n"
                response_data += hexdump(response.content[:200])
                if content_length > 200:
                    response_data += "\n... (truncated)"
        
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response": response_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing API request: {str(e)}")
    
    
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
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interpreting API response: {str(e)}")


def is_readable_text(text, readable_threshold=0.8):
    """
    Check if a string appears to be human-readable text.
    Returns True if the proportion of printable ASCII characters exceeds the threshold.
    """
    if not text:
        return True
        
    printable = sum(c.isascii() and (c.isprintable() or c.isspace()) for c in text)
    return printable / len(text) >= readable_threshold


def hexdump(data, bytes_per_line=16):
    """
    Create a hexdump representation of binary data.
    """
    result = []
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i:i + bytes_per_line]
        hex_part = ' '.join(f'{b:02X}' for b in chunk)
        # Create ASCII representation (printable chars only)
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        result.append(f'{i:08X}:  {hex_part.ljust(bytes_per_line*3)}  {ascii_part}')
    return '\n'.join(result)