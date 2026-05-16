from __future__ import annotations

from pathlib import Path

from waste_app import create_app
from waste_app.config import Config


class TestConfig(Config):
    TESTING = True
    DATABASE_PATH = Config.BASE_DIR / "instance/test.sqlite3"
    UPLOAD_FOLDER = Config.BASE_DIR / "uploads/test"


def test_health_endpoint():
    app = create_app(TestConfig)
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["ok"] is True


def test_quiz_bank_has_at_least_twenty_questions():
    app = create_app(TestConfig)
    client = app.test_client()
    response = client.get("/api/quiz?count=20")
    data = response.get_json()
    assert response.status_code == 200
    assert data["total_bank_size"] >= 20
    assert len(data["data"]) == 20
    assert "answer" not in data["data"][0]


def test_search_returns_known_item():
    app = create_app(TestConfig)
    client = app.test_client()
    response = client.get("/api/search?q=电池")
    data = response.get_json()
    assert response.status_code == 200
    assert data["ok"] is True
    assert any(item["category"] == "hazardous" for item in data["data"])


def test_missing_model_returns_clear_error(tmp_path: Path):
    app = create_app(TestConfig)
    client = app.test_client()
    image = tmp_path / "sample.jpg"
    image.write_bytes(b"not-real-image-but-extension-is-valid")
    with image.open("rb") as f:
        response = client.post("/api/recognize", data={"image": (f, "sample.jpg")}, content_type="multipart/form-data")
    assert response.status_code == 503
    assert "模型未就绪" in response.get_json()["message"]
