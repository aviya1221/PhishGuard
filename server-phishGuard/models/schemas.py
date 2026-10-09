from typing import Literal

from pydantic import BaseModel, Field


class AnalysisResponse(BaseModel):
    """Response model for phishing analysis results."""
    score: int = Field(ge=1, le=10)
    verdict: Literal["Safe", "Suspicious", "Phishing"]
    red_flags: list[str]
    recommendation: str
