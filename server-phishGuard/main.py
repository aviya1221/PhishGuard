import os
import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# Load environment variables before importing services that read them at import time
load_dotenv()

from models.schemas import AnalysisResponse
from services.gemini_service import gemini_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="PhishGuard API", version="1.0.0")

# Configure CORS
origins = [
    "http://localhost:5173",  # Local development React frontend
    "http://localhost:3000",  # Fallback local port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # allow_origins only matches exact strings, so wildcards must go through a regex
    allow_origin_regex=r"https://[a-z0-9-]+\.netlify\.app",  # Production Netlify URL pattern
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/")
async def root():
    return {"message": "PhishGuard API is running"}


# Main analysis endpoint
@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    language: str = Form("en")
):
    """
    Analyze an uploaded image for phishing indicators using Gemini 1.5 Flash.
    
    Ephemeral Processing: Image is read directly into memory (RAM) 
    and never persisted to disk.
    
    Args:
        file: UploadFile containing the image to analyze
        language: Language code for the response (default: "en")
    
    Returns:
        AnalysisResponse: Analysis results with score, verdict, red flags, and recommendation
    """
    # Read file directly into memory (Ephemeral Processing)
    file_content = await file.read()
    
    # Verify the file is not empty
    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded. Please provide a valid image file."
        )
    
    # Delegate to Gemini service for analysis
    analysis = await gemini_service.analyze_image(
        file_content=file_content,
        mime_type=file.content_type or "image/jpeg",
        language=language
    )
    
    return analysis


if __name__ == "__main__":
    # Dynamic port binding for Render and other deployment platforms
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
