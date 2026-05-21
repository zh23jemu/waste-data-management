from __future__ import annotations

import random
import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from .knowledge import HOT_KEYWORDS, QUESTIONS, search_knowledge
from .services.deepseek_service import ExternalApiError, ask_deepseek
from .services.history_service import add_history, clear_history, delete_history, list_history
from .services.kimi_service import analyze_image_with_kimi
from .services.model_service import ModelNotReadyError, WasteClassifier
from .services.similarity_service import SimilaritySearchError, SimilarityService

api_bp = Blueprint("api", __name__)
_classifier_cache: WasteClassifier | None = None


def error_response(message: str, status: int = 400):
    """统一错误响应格式，前端可直接展示 message。"""
    return jsonify({"ok": False, "message": message}), status


def allowed_file(filename: str) -> bool:
    """校验图片扩展名是否符合任务书要求。"""
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return suffix in current_app.config["ALLOWED_EXTENSIONS"]


def save_upload(field_name: str = "image") -> Path:
    """保存上传图片并返回本地路径。"""
    file = request.files.get(field_name)
    if file is None or not file.filename:
        raise ValueError("请上传图片文件。")
    if not allowed_file(file.filename):
        raise ValueError("仅支持 PNG、JPG、JPEG 格式图片。")

    upload_dir: Path = current_app.config["UPLOAD_FOLDER"]
    upload_dir.mkdir(parents=True, exist_ok=True)
    original = secure_filename(file.filename)
    suffix = Path(original).suffix.lower()
    filename = f"{uuid.uuid4().hex}{suffix}"
    target = upload_dir / filename
    file.save(target)
    return target


def classifier() -> WasteClassifier:
    """获取全局分类器实例，避免每个请求重复构造对象。"""
    global _classifier_cache
    if _classifier_cache is None:
        _classifier_cache = WasteClassifier(current_app.config["MODEL_PATH"], current_app.config["CLASS_MAP_PATH"])
    return _classifier_cache


@api_bp.get("/config")
def api_config():
    """返回前端需要展示的非敏感配置。"""
    return jsonify({
        "ok": True,
        "max_upload_mb": current_app.config["MAX_CONTENT_LENGTH"] // 1024 // 1024,
        "allowed_extensions": sorted(current_app.config["ALLOWED_EXTENSIONS"]),
        "similarity_threshold": current_app.config["SIMILARITY_THRESHOLD"],
    })


@api_bp.post("/recognize")
def recognize():
    """图像识别接口：上传图片后返回四分类结果并写入历史记录。"""
    try:
        image_path = save_upload("image")
        result = classifier().predict(image_path)
        result["image_path"] = str(image_path.relative_to(current_app.config["BASE_DIR"]))
        result["history_id"] = add_history(current_app.config["DATABASE_PATH"], result["image_path"], result)
        return jsonify({"ok": True, "data": result})
    except ModelNotReadyError as exc:
        return error_response(str(exc), 503)
    except RequestEntityTooLarge:
        max_mb = current_app.config["MAX_CONTENT_LENGTH"] // 1024 // 1024
        return error_response(f"上传文件不能超过 {max_mb}MB。", 413)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(f"识别失败：{exc}", 500)


@api_bp.post("/similar-search")
def similar_search():
    """相似图片检索接口。"""
    try:
        image_path = save_upload("image")
        service = SimilarityService(
            classifier(),
            current_app.config["QDRANT_URL"],
            current_app.config["QDRANT_COLLECTION"],
            current_app.config["SIMILARITY_THRESHOLD"],
        )
        return jsonify({"ok": True, "data": service.search(image_path)})
    except (ModelNotReadyError, SimilaritySearchError) as exc:
        return error_response(str(exc), 503)
    except RequestEntityTooLarge:
        max_mb = current_app.config["MAX_CONTENT_LENGTH"] // 1024 // 1024
        return error_response(f"上传文件不能超过 {max_mb}MB。", 413)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        return error_response(f"相似搜索失败：{exc}", 500)


@api_bp.get("/search")
def text_search():
    """文字检索接口。"""
    keyword = request.args.get("q", "")
    return jsonify({"ok": True, "data": search_knowledge(keyword), "hot_keywords": HOT_KEYWORDS})


@api_bp.post("/chat")
def chat():
    """DeepSeek 智能交流接口。"""
    payload = request.get_json(silent=True) or {}
    try:
        answer = ask_deepseek(
            payload.get("question", ""),
            api_key=current_app.config["DEEPSEEK_API_KEY"],
            base_url=current_app.config["DEEPSEEK_BASE_URL"],
            model=current_app.config["DEEPSEEK_MODEL"],
        )
        return jsonify({"ok": True, "data": {"answer": answer}})
    except ExternalApiError as exc:
        return error_response(str(exc), 503)


@api_bp.post("/image-understanding")
def image_understanding():
    """Kimi 多模态图片理解接口。"""
    try:
        image_path = save_upload("image")
        answer = analyze_image_with_kimi(
            image_path,
            api_key=current_app.config["KIMI_API_KEY"],
            base_url=current_app.config["KIMI_BASE_URL"],
            model=current_app.config["KIMI_MODEL"],
        )
        return jsonify({"ok": True, "data": {"answer": answer}})
    except ExternalApiError as exc:
        return error_response(str(exc), 503)
    except RequestEntityTooLarge:
        max_mb = current_app.config["MAX_CONTENT_LENGTH"] // 1024 // 1024
        return error_response(f"上传文件不能超过 {max_mb}MB。", 413)
    except ValueError as exc:
        return error_response(str(exc), 400)


@api_bp.get("/history")
def history_list():
    """分页查看历史记录。"""
    page = int(request.args.get("page", "1"))
    page_size = int(request.args.get("page_size", "10"))
    return jsonify({"ok": True, "data": list_history(current_app.config["DATABASE_PATH"], page, page_size)})


@api_bp.delete("/history/<int:record_id>")
def history_delete(record_id: int):
    """删除单条历史记录。"""
    deleted = delete_history(current_app.config["DATABASE_PATH"], record_id)
    return jsonify({"ok": True, "deleted": deleted})


@api_bp.delete("/history")
def history_clear():
    """清空全部历史记录。"""
    return jsonify({"ok": True, "deleted": clear_history(current_app.config["DATABASE_PATH"])})


@api_bp.get("/quiz")
def quiz_questions():
    """随机返回知识测试题目，默认 10 道。"""
    count = min(max(int(request.args.get("count", "10")), 1), len(QUESTIONS))
    selected = random.sample(QUESTIONS, count)
    public_questions = [{k: v for k, v in item.items() if k != "answer"} for item in selected]
    return jsonify({"ok": True, "data": public_questions, "total_bank_size": len(QUESTIONS)})


@api_bp.post("/quiz/submit")
def quiz_submit():
    """提交知识测试答案并返回得分和解析。"""
    payload = request.get_json(silent=True) or {}
    answers = {int(item["id"]): item.get("answer", "") for item in payload.get("answers", []) if "id" in item}
    question_map = {item["id"]: item for item in QUESTIONS}
    details = []
    correct = 0
    for qid, user_answer in answers.items():
        question = question_map.get(qid)
        if not question:
            continue
        is_correct = user_answer == question["answer"]
        correct += int(is_correct)
        details.append({
            "id": qid,
            "question": question["question"],
            "user_answer": user_answer,
            "correct_answer": question["answer"],
            "is_correct": is_correct,
            "explanation": question["explanation"],
        })
    total = len(details)
    score = round(correct / total * 100, 2) if total else 0
    return jsonify({"ok": True, "data": {"score": score, "correct": correct, "total": total, "details": details}})
