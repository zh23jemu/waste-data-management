from __future__ import annotations

from pathlib import Path
from io import BytesIO

from waste_app import create_app
from waste_app.config import Config
from waste_app.services.history_service import add_history


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


def test_upload_rejects_invalid_file_type():
    """上传接口应拒绝任务书范围外的文件格式，并给出明确中文提示。"""
    app = create_app(TestConfig)
    client = app.test_client()
    response = client.post(
        "/api/recognize",
        data={"image": (BytesIO(b"plain text"), "note.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert "仅支持 PNG、JPG、JPEG" in response.get_json()["message"]


def test_upload_rejects_oversized_file():
    """上传文件超过 16MB 时，应返回 JSON 错误而不是默认 HTML 错误页。"""
    app = create_app(TestConfig)
    client = app.test_client()
    oversized = BytesIO(b"0" * (17 * 1024 * 1024))
    response = client.post(
        "/api/recognize",
        data={"image": (oversized, "large.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 413
    assert "上传文件不能超过" in response.get_json()["message"]


def test_chat_without_deepseek_key_returns_readable_error():
    """DeepSeek 未配置密钥时，接口应可读失败且不导致服务崩溃。"""
    app = create_app(TestConfig)
    client = app.test_client()
    response = client.post("/api/chat", json={"question": "电池怎么分类？"})
    assert response.status_code == 503
    assert "DEEPSEEK_API_KEY" in response.get_json()["message"]


def test_image_understanding_without_xunfei_config_returns_readable_error():
    """星火图片理解缺少配置时，应返回清晰错误，便于演示前补齐 .env。"""
    app = create_app(TestConfig)
    client = app.test_client()
    response = client.post(
        "/api/image-understanding",
        data={"image": (BytesIO(b"fake image"), "sample.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 503
    assert "星火图片理解配置不完整" in response.get_json()["message"]


def test_quiz_submit_scores_answers():
    """知识测试提交后应返回得分、正确数和逐题解析。"""
    app = create_app(TestConfig)
    client = app.test_client()
    response = client.post(
        "/api/quiz/submit",
        json={"answers": [{"id": 1, "answer": "有害垃圾"}, {"id": 2, "answer": "其他垃圾"}]},
    )
    data = response.get_json()["data"]
    assert response.status_code == 200
    assert data["total"] == 2
    assert data["correct"] == 1
    assert data["score"] == 50.0
    assert data["details"][0]["explanation"]


def test_history_list_delete_and_clear(tmp_path: Path):
    """历史记录模块应支持新增后的分页查询、单条删除和清空。"""
    class IsolatedConfig(TestConfig):
        DATABASE_PATH = tmp_path / "history.sqlite3"
        UPLOAD_FOLDER = tmp_path / "uploads"

    app = create_app(IsolatedConfig)
    client = app.test_client()
    first_id = add_history(
        app.config["DATABASE_PATH"],
        "uploads/test/a.jpg",
        {"predicted_class": "recyclable", "confidence": 0.91, "probabilities": {"recyclable": 0.91}, "rationale": "测试记录"},
    )
    second_id = add_history(
        app.config["DATABASE_PATH"],
        "uploads/test/b.jpg",
        {"predicted_class": "hazardous", "confidence": 0.82, "probabilities": {"hazardous": 0.82}, "rationale": "测试记录"},
    )

    list_response = client.get("/api/history?page=1&page_size=1")
    list_data = list_response.get_json()["data"]
    assert list_response.status_code == 200
    assert list_data["total"] == 2
    assert len(list_data["items"]) == 1
    assert list_data["items"][0]["id"] == second_id

    delete_response = client.delete(f"/api/history/{first_id}")
    assert delete_response.status_code == 200
    assert delete_response.get_json()["deleted"] is True

    clear_response = client.delete("/api/history")
    assert clear_response.status_code == 200
    assert clear_response.get_json()["deleted"] == 1
