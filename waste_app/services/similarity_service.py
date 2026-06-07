from __future__ import annotations

from pathlib import Path
from typing import Any

from .model_service import ModelNotReadyError, WasteClassifier


class SimilaritySearchError(RuntimeError):
    """相似搜索不可用时抛出的业务异常。"""


class SimilarityService:
    """基于 Qdrant 的图片相似搜索服务。

    相似检索面向演示场景时，更适合展示 Top-N 候选结果，而不是只返回高阈值
    命中的图片。这样用户上传数据集内的图片时，第一条可以看到接近 100% 的
    原图命中，后续也能看到相似度逐渐降低的参考案例。
    """

    def __init__(self, classifier: WasteClassifier, qdrant_url: str, collection: str, threshold: float, limit: int = 12):
        self.classifier = classifier
        self.qdrant_url = qdrant_url
        self.collection = collection
        self.threshold = threshold
        self.limit = limit

    def _client(self):
        try:
            from qdrant_client import QdrantClient
        except Exception as exc:
            raise SimilaritySearchError(f"qdrant-client 依赖未安装或不可用：{exc}") from exc
        return QdrantClient(url=self.qdrant_url)

    def search(self, image_path: Path, limit: int | None = None) -> list[dict[str, Any]]:
        """检索 Top-N 相似图片。

        `threshold` 只作为可配置的最低返回线，默认值为 0.0，避免 Qdrant 在服务端
        过早过滤掉 80%、60%、50% 这类对演示仍有解释价值的候选图片。
        """
        try:
            vector = self.classifier.extract_feature(image_path)
        except ModelNotReadyError:
            raise
        except Exception as exc:
            raise SimilaritySearchError(f"图片特征提取失败：{exc}") from exc
        try:
            client = self._client()
            search_limit = limit or self.limit
            if hasattr(client, "query_points"):
                # qdrant-client 新版本使用 query_points 接口，返回值会把命中结果放在 points 字段。
                response = client.query_points(
                    collection_name=self.collection,
                    query=vector,
                    limit=search_limit,
                    with_payload=True,
                    score_threshold=self.threshold,
                )
                results = response.points
            else:
                # 兼容旧版本 qdrant-client，避免部署环境依赖版本较旧时相似检索不可用。
                results = client.search(
                    collection_name=self.collection,
                    query_vector=vector,
                    limit=search_limit,
                    score_threshold=self.threshold,
                    with_payload=True,
                )
        except Exception as exc:
            raise SimilaritySearchError(f"Qdrant 检索失败，请确认服务和集合已初始化：{exc}") from exc

        sorted_results = sorted(results, key=lambda hit: float(hit.score), reverse=True)
        items = []
        for rank, hit in enumerate(sorted_results, start=1):
            score = float(hit.score)
            if score >= self.threshold:
                items.append({
                    "id": hit.id,
                    "rank": rank,
                    "score": score,
                    "is_exact_match": score >= 0.999,
                    "payload": hit.payload or {},
                })
        return items
