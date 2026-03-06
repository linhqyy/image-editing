import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

# Prevent .env from overriding test env
import os
os.environ.setdefault("RUNPOD_API_KEY", "test-key")
os.environ.setdefault("RUNPOD_ENDPOINT_ID", "test-endpoint")
os.environ.setdefault("OTEL_ENABLED", "false")

from main import app

client = TestClient(app)


# ── /health ─────────────────────────────────────────────────────────────────

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── /debug-workflow ──────────────────────────────────────────────────────────

def test_debug_workflow_returns_keys():
    response = client.get("/debug-workflow")
    assert response.status_code == 200
    data = response.json()
    assert "UPLOAD_IMAGE_NAME" in data
    assert "node_76_image_input" in data


# ── /edit-image ──────────────────────────────────────────────────────────────

def test_edit_image_no_file_returns_422():
    """Missing file field → FastAPI validation error."""
    response = client.post("/edit-image")
    assert response.status_code == 422


def test_edit_image_empty_file_returns_400():
    """Empty bytes → our explicit 400."""
    response = client.post(
        "/edit-image",
        files={"image": ("empty.png", b"", "image/png")},
    )
    assert response.status_code == 400


def test_edit_image_success():
    """Happy path — RunPod returns fake PNG bytes."""
    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    with patch("main.call_runsync", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = fake_png
        response = client.post(
            "/edit-image",
            files={"image": ("test.png", b"fake-image-data", "image/png")},
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == fake_png


def test_edit_image_runpod_error_returns_502():
    """RunPod raises RuntimeError → 502."""
    with patch("main.call_runsync", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = RuntimeError("job failed")
        response = client.post(
            "/edit-image",
            files={"image": ("test.png", b"fake-image-data", "image/png")},
        )

    assert response.status_code == 502
