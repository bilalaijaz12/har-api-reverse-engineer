from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import json
import uuid
from datetime import datetime

# Import the session storage from storage module
from utils.storage import session_storage

# Import HAR processing utilities
from utils.har_processor import process_har_file

router = APIRouter(
    prefix="/api",
    tags=["upload"],
)

@router.post("/upload")
async def upload_har(file: UploadFile = File(...)):
    """
    Upload and process a HAR file.
    
    Returns a session ID that can be used to reference this HAR file in future requests.
    """
    # Check if file is a HAR file
    if not file.filename.endswith(".har"):
        raise HTTPException(status_code=400, detail="File must be a .har file")
    
    try:
        # Read the file content
        content = await file.read()
        
        # Process the HAR file to extract API requests
        processed_data = process_har_file(content)
        
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Store the processed data with the session ID
        session_storage[session_id] = {
            "processed_har": processed_data,
            "timestamp": datetime.now()
        }
        
        return {
            "session_id": session_id,
            "message": "HAR file processed successfully",
            "api_count": len(processed_data)
        }
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid HAR file format. Cannot parse JSON.")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing HAR file: {str(e)}")