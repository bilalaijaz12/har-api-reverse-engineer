from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="HAR API Reverse Engineer",
    description="Extract API requests from HAR files using LLMs",
    version="0.1.0"
)

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint to check if the API is running"""
    return {"message": "HAR API Reverse Engineer backend is running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

# Import routes after app creation
from routes import upload, analyze, test

# Register routes
app.include_router(upload.router)
app.include_router(analyze.router)
app.include_router(test.router)

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)