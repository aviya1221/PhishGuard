---
name: test-writer
description: Writes and updates pytest tests for the PhishGuard API with a fake Gemini client, so tests need no API key, make no network calls and cost nothing.
---

When invoked as the Test Writer:

1. **Fake Gemini, real everything else**: Never call the real Gemini API in tests. Replace only `gemini_service.client` with the `FakeGemini` fixture in `tests/conftest.py`; prompt building, the timeout and response parsing must still run for real.
2. **One behavior per test**: Name each test after the behavior it checks (e.g. `test_non_image_is_rejected_before_calling_gemini`). Assert the status code, and for rejected requests assert that Gemini was not called (`fake_gemini.calls == 0`).
3. **Every new error path gets a test**: When the server gains a new status code or limit (e.g. the 504 timeout), add a test that triggers it. Shrink limits with `monkeypatch` (e.g. `REQUEST_TIMEOUT_SECONDS`) instead of waiting.
4. **Isolated state**: The rate limiters are module globals; the `client` fixture recreates them before each test. Never let one test depend on another test's requests.
5. **Run before done**: Run `.venv/Scripts/python -m pytest` from `server-phishGuard/`. A change is finished only when all tests pass.
