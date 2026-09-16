from pydantic import BaseModel


class AnalysisResponse(BaseModel):
    """Response model for phishing analysis results."""
    score: int
    verdict: str
    red_flags: list[str]
    recommendation: str
