import os
import logging
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.formparsers import MultiPartParser
import uvicorn
from dotenv import load_dotenv

# Load environment variables before importing services that read them at import time
load_dotenv()

from models.schemas import AnalysisResponse
from services.gemini_service import gemini_service, SUPPORTED_LANGUAGES
from services.rate_limiter import RateLimiter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Upload limits
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
MULTIPART_OVERHEAD_BYTES = 64 * 1024  # Multipart boundaries, part headers and the language field

# Starlette spools uploads larger than 1 MB to a temp file on disk.
# Raise the threshold above the upload limit so images always stay in RAM (Ephemeral Processing).
MultiPartParser.spool_max_size = MAX_UPLOAD_BYTES + MULTIPART_OVERHEAD_BYTES

# Rate limits for /api/analyze. The global limit is a backstop that protects the
# Gemini quota even if a client spoofs X-Forwarded-For to dodge the per-IP limit.
per_ip_limiter = RateLimiter(max_requests=10, window_seconds=60)
global_limiter = RateLimiter(max_requests=30, window_seconds=60)

# Image signatures (magic bytes) mapped to their MIME types
IMAGE_SIGNATURES = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
}


def detect_image_mime_type(data: bytes) -> str | None:
    """Return the MIME type based on the file's magic bytes, or None if it isn't PNG/JPEG."""
    for signature, mime_type in IMAGE_SIGNATURES.items():
        if data.startswith(signature):
            return mime_type
    return None


# Initialize FastAPI app
app = FastAPI(title="PhishGuard API", version="1.0.0")


# Registered before CORSMiddleware so CORS wraps these early responses too
# (middleware added later runs first). Without CORS headers the browser would
# hide the real status behind a CORS error.
@app.middleware("http")
async def guard_analyze_requests(request: Request, call_next):
    """Reject oversized and rate-limited analyze requests before the body is parsed."""
    if request.method == "POST" and request.url.path == "/api/analyze":
        content_length = request.headers.get("content-length")
        if content_length is None or not content_length.isdigit():
            return JSONResponse(
                status_code=status.HTTP_411_LENGTH_REQUIRED,
                content={"detail": "Content-Length header is required."}
            )
        if int(content_length) > MAX_UPLOAD_BYTES + MULTIPART_OVERHEAD_BYTES:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": f"File is too large. Maximum size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB."}
            )

        # Check the per-IP limit first so a single noisy client doesn't use up the global budget
        client_ip = request.client.host if request.client else "unknown"
        if not per_ip_limiter.allow(client_ip) or not global_limiter.allow("global"):
            logger.warning(f"Rate limit reached for {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please wait a minute and try again."},
                headers={"Retry-After": "60"}
            )

    return await call_next(request)


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
    Analyze an uploaded image for phishing indicators using Gemini 2.5 Flash-Lite.

    Ephemeral Processing: Image is read directly into memory (RAM)
    and never persisted to disk.

    Args:
        file: UploadFile containing the image to analyze (PNG or JPEG, up to 10 MB)
        language: Language code for the response, one of SUPPORTED_LANGUAGES (default: "en")

    Returns:
        AnalysisResponse: Analysis results with score, verdict, red flags, and recommendation
    """
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language. Use one of: {', '.join(SUPPORTED_LANGUAGES)}."
        )

    # Read file directly into memory (Ephemeral Processing)
    file_content = await file.read()

    # Verify the file is not empty
    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded. Please provide a valid image file."
        )

    if len(file_content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File is too large. Maximum size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
        )

    # Trust the file's actual bytes, not the client-provided Content-Type
    mime_type = detect_image_mime_type(file_content)
    if mime_type is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type. Please upload a PNG or JPEG image."
        )

    # Delegate to Gemini service for analysis
    analysis = await gemini_service.analyze_image(
        file_content=file_content,
        mime_type=mime_type,
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
        log_level="info",
        # Behind Render's proxy, read the real client IP from X-Forwarded-For (used by the rate limiter)
        forwarded_allow_ips="*"
    )
