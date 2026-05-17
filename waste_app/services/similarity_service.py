from __future__ import annotations

from pathlib import Path
from typing import Any

from .model_service import ModelNotReadyError, WasteClassifier


class SimilaritySearchError(RuntimeError):
    """相似搜索不可用时抛出的业务异常。"""


class SimilarityService:
    """基于 Qdrant 的图片相似搜索服务。"""

    def __init__(self, classifier: WasteClassifier, qdrant_url: str, collection: str, threshold: float):
        self.classifier = classifier
        self.qdrant_url = qdrant_url
        self.collection = collection
        self.threshold = threshold

    def _client(self):
        try:
            from qdrant_client import QdrantClient
        except Exception as exc:
            raise SimilaritySearchError(f"qdrant-client 依赖未安装或不可用：{exc}") from exc
        return QdrantClient(url=self.qdrant_url)

    def search(self, image_path: Path, limit: int = 5) -> list[dict[str, Any]]:
        """检索相似度大于阈值的历史参考图片。"""
        try:
            vector = self.classifier.extract_feature(image_path)
        except ModelNotReadyError:
            raise
        except Exception as exc:
            raise SimilaritySearchError(f"图片特征提取失败：{exc}") from exc
        try:
            client = self._client()
            if hasattr(client, "query_points"):
                # qdrant-client 新版本使用 query_points 接口，返回值会把命中结果放在 points 字段。
                # 这里显式传入 score_threshold，让服务端先过滤低于阈值的结果，减少后续 Python 端处理。
                response = client.query_points(
                    collection_name=self.collection,
                    query=vector,
                    limit=limit,
                    with_payload=True,
                    score_threshold=self.threshold,
                )
                results = response.points
            else:
                # 兼容旧版本 qdrant-client，避免部署环境依赖版本较旧时相似检索不可用。
                results = client.search(
                    collection_name=self.collection,
                    query_vector=vector,
                    limit=limit,
                    score_threshold=self.threshold,
                    with_payload=True,
                )
        except Exception as exc:
            raise SimilaritySearchError(f"Qdrant 检索失败，请确认服务和集合已初始化：{exc}") from exc

        items = []
        for hit in results:
            score = float(hit.score)
            if score >= self.threshold:
                items.append({"id": hit.id, "score": score, "payload": hit.payload or {}})
        return items
