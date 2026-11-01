"""Tests for POST /api/analyze with Gemini replaced by a fake: no API key, no network, no cost."""
import main
import services.gemini_service as gemini_module

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


def post_image(client, data=PNG, language="he"):
    return client.post("/api/analyze", files={"file": ("message.png", data, "image/png")}, data={"language": language})


def test_valid_image_returns_analysis(client, fake_gemini):
    response = post_image(client)

    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 9
    assert body["verdict"] == "Phishing"
    assert body["red_flags"] == ["Fake link"]
    assert body["recommendation"]
    assert fake_gemini.calls == 1


def test_non_image_is_rejected_before_calling_gemini(client, fake_gemini):
    # The client says image/png, but the bytes are text: the magic bytes check must win
    response = post_image(client, data=b"this is not an image")

    assert response.status_code == 415
    assert fake_gemini.calls == 0


def test_oversized_request_is_rejected_by_content_length(client, fake_gemini):
    # Caught by the middleware from the header, before the body is parsed
    data = PNG + b"\x00" * (main.MAX_UPLOAD_BYTES + main.MULTIPART_OVERHEAD_BYTES)

    response = post_image(client, data=data)

    assert response.status_code == 413
    assert fake_gemini.calls == 0


def test_file_just_over_the_limit_is_rejected(client, fake_gemini):
    # Small enough to pass the middleware's overhead allowance, so the endpoint's own check catches it
    data = PNG + b"\x00" * (main.MAX_UPLOAD_BYTES + 1 - len(PNG))

    response = post_image(client, data=data)

    assert response.status_code == 413
    assert fake_gemini.calls == 0


def test_empty_file_is_rejected(client, fake_gemini):
    response = post_image(client, data=b"")

    assert response.status_code == 400
    assert fake_gemini.calls == 0


def test_unsupported_language_is_rejected(client, fake_gemini):
    response = post_image(client, language="fr")

    assert response.status_code == 400
    assert fake_gemini.calls == 0


def test_broken_json_from_gemini_returns_502(client, fake_gemini):
    fake_gemini.text = '{"score": 9, "verdict": '

    response = post_image(client)

    assert response.status_code == 502


def test_eleventh_request_in_a_minute_is_rate_limited(client, fake_gemini):
    for _ in range(main.per_ip_limiter.max_requests):
        assert post_image(client).status_code == 200

    response = post_image(client)

    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"
    assert fake_gemini.calls == main.per_ip_limiter.max_requests


def test_slow_gemini_times_out_with_504(client, fake_gemini, monkeypatch):
    monkeypatch.setattr(gemini_module, "REQUEST_TIMEOUT_SECONDS", 0.05)
    fake_gemini.delay = 1.0

    response = post_image(client)

    assert response.status_code == 504
