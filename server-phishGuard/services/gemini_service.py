import json
import logging
import os
from fastapi import HTTPException, status
from google import genai
from google.genai import types
from pydantic import ValidationError

from models.schemas import AnalysisResponse

logger = logging.getLogger(__name__)

# Base system prompt for phishing detection
PHISHING_DETECTION_PROMPT_BASE = """You are an expert phishing detection analyst specializing in visual and textual analysis of screenshots and images.

## ANALYSIS FRAMEWORK

### 1. VISUAL ANALYSIS:
- Brand Consistency: Look for mismatched logos, fonts, or color schemes
- UI/UX Patterns: Identify suspicious button placements, form layouts, or unusual design elements
- Security Indicators: Check for missing HTTPS, padlock icons, or security warnings
- Layout Anomalies: Spot unusual spacing, overlapping elements, or poor alignment
- Visual Urgency Cues: Red banners, warning icons, or pressure tactics

### 2. TEXTUAL/OCR ANALYSIS:
- Social Engineering Language: Urgent calls to action ("Act now!", "Verify immediately")
- Threat Messaging: Claims of account suspension, security threats, or unusual activity
- Grammar & Spelling: Poor grammar, misspellings, or awkward phrasing
- Domain/Email Indicators: Suspicious email addresses, mismatched domains
- Urgency Markers: Time-sensitive language, artificial scarcity, deadline pressure

## OUTPUT FORMAT (STRICT JSON ONLY):
Return ONLY a valid JSON object with NO additional text, explanation, or markdown. The JSON must contain:
{{
  "score": <integer between 1-10, where 1=definitely safe, 10=definitely phishing>,
  "verdict": <exactly one of: "Safe", "Suspicious", or "Phishing" - always in English>,
  "red_flags": [<list of specific red flags detected, empty list if none>],
  "recommendation": <actionable security recommendation for the user>
}}

## VERDICT GUIDELINES:
- "Safe" (score 1-3): No red flags; legitimate appearance
- "Suspicious" (score 4-7): Multiple concerning indicators or unclear intent
- "Phishing" (score 8-10): Strong phishing indicators; high confidence threat

## CRITICAL RULES:
1. Return ONLY valid JSON, no markdown, no code blocks, no explanation
2. All fields must be present
3. "red_flags" must be a list of strings (can be empty)
4. "score" must be an integer between 1 and 10
5. "verdict" must be exactly one of the three allowed values

## LANGUAGE REQUIREMENT:
You must write the values for 'red_flags' and 'recommendation' strictly in the following language: {language}. The 'verdict' value MUST always be exactly "Safe", "Suspicious", or "Phishing" in English, regardless of the language. The JSON keys MUST remain exactly in English as defined in the schema."""


# Supported language codes mapped to the language name given to the model
SUPPORTED_LANGUAGES = {
    "en": "English",
    "he": "Hebrew",
}


def get_phishing_detection_prompt(language: str = "en") -> str:
    """
    Generate a phishing detection prompt with language specification.

    Args:
        language: Language code, one of SUPPORTED_LANGUAGES (e.g., "en", "he")

    Returns:
        System prompt with the language name injected (falls back to English)
    """
    return PHISHING_DETECTION_PROMPT_BASE.format(language=SUPPORTED_LANGUAGES.get(language, "English"))


class GeminiService:
    """Service for interacting with Google Gemini API for phishing detection."""

    def __init__(self):
        """Initialize the Gemini service with API key."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None

        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment. AI analysis will be unavailable.")
        else:
            self.client = genai.Client(api_key=self.api_key)

    def is_available(self) -> bool:
        """Check if Gemini service is available and configured."""
        return self.client is not None

    async def analyze_image(
        self,
        file_content: bytes,
        mime_type: str = "image/jpeg",
        language: str = "en"
    ) -> AnalysisResponse:
        """
        Analyze an image for phishing indicators using Gemini 3.5 Flash-Lite.

        Args:
            file_content: Image file content as bytes
            mime_type: MIME type of the image (default: image/jpeg)
            language: Language code for the response (default: "en")

        Returns:
            AnalysisResponse: Analysis results with score, verdict, red flags, and recommendation

        Raises:
            HTTPException: If API is unavailable or analysis fails
        """
        if not self.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI analysis service is not available. Please configure GEMINI_API_KEY."
            )

        try:
            # Create image part directly from bytes
            image_part = types.Part.from_bytes(data=file_content, mime_type=mime_type)

            # Get the language-specific prompt
            prompt = get_phishing_detection_prompt(language)

            # Call Gemini model with vision capabilities and JSON mode.
            # Use the async client so the event loop isn't blocked while waiting.
            response = await self.client.aio.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=[
                    prompt,
                    image_part,
                    "Analyze this image for phishing indicators. Return ONLY valid JSON."
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )

            # Extract response text
            if not response.text:
                raise ValueError("No response received from AI model")

            logger.info(f"Gemini response: {response.text[:200]}...")

            # Parse and validate response (JSON mode guarantees valid JSON)
            analysis = self._parse_response(response.text)
            return analysis

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"AI analysis error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI analysis failed: {str(e)}"
            )

    def _parse_response(self, response_text: str) -> AnalysisResponse:
        """
        Parse and validate Gemini response JSON.

        Args:
            response_text: Raw response text from Gemini model (guaranteed JSON)

        Returns:
            AnalysisResponse: Validated analysis response

        Raises:
            HTTPException: If JSON parsing or validation fails
        """
        try:
            # Parse JSON directly (no markdown stripping needed with JSON mode)
            ai_response = json.loads(response_text)

            # Validate response structure
            analysis = AnalysisResponse(
                score=int(ai_response.get("score", 5)),
                verdict=str(ai_response.get("verdict", "Suspicious")),
                red_flags=ai_response.get("red_flags", []),
                recommendation=str(ai_response.get("recommendation", "Review this content carefully."))
            )

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {response_text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI model returned invalid JSON: {str(e)}"
            )
        except ValidationError as e:
            logger.error(f"Response validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI response did not match expected format"
            )


# Global instance
gemini_service = GeminiService()
