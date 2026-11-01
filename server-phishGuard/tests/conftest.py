import asyncio
import os
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

# Never use the real key: load_dotenv in main.py does not override a variable that is already set
os.environ["GEMINI_API_KEY"] = "test-key"

import main  # noqa: E402
import services.gemini_service as gemini_module  # noqa: E402
from services.rate_limiter import RateLimiter  # noqa: E402

VALID_ANSWER = '{"score": 9, "verdict": "Phishing", "red_flags": ["Fake link"], "recommendation": "Do not click."}'


class FakeGemini:
    """Stands in for genai.Client: counts calls and returns a canned answer, optionally after a delay."""

    def __init__(self):
        self.calls = 0
        self.text = VALID_ANSWER
        self.delay = 0.0
        self.aio = SimpleNamespace(models=SimpleNamespace(generate_content=self.generate_content))

    async def generate_content(self, **kwargs):
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        return SimpleNamespace(text=self.text, usage_metadata=None)


@pytest.fixture
def fake_gemini(monkeypatch):
    """Swap only the Gemini client; prompt building, timeout and response parsing stay real."""
    fake = FakeGemini()
    monkeypatch.setattr(gemini_module.gemini_service, "client", fake)
    return fake


@pytest.fixture
def client(fake_gemini, monkeypatch):
    # Fresh limiters with the same settings, so requests from one test don't count against another
    for name in ("per_ip_limiter", "global_limiter"):
        limiter = getattr(main, name)
        monkeypatch.setattr(main, name, RateLimiter(limiter.max_requests, limiter.window_seconds))
    return TestClient(main.app)
