from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image

from ..knowledge import CATEGORY_LABELS, CLASS_RATIONALES


class ModelNotReadyError(RuntimeError):
    """模型文件或深度学习依赖未准备好时抛出的业务异常。"""


class WasteClassifier:
    """ResNet50 四分类推理服务。"""

    def __init__(self, model_path: Path, class_map_path: Path):
        self.model_path = model_path
        self.class_map_path = class_map_path
        self._model = None
        self._feature_model = None
        self._transform = None
        self._device = None
        self._classes: list[str] | None = None

    def _load(self) -> None:
        """懒加载模型权重和类别映射。"""
        if self._model is not None:
            return
        if not self.model_path.exists() or not self.class_map_path.exists():
            raise ModelNotReadyError("模型未就绪：请先运行 scripts/train_resnet50.py 生成模型权重和类别映射。")
        try:
            import torch
            from torchvision import models, transforms
        except Exception as exc:
            raise ModelNotReadyError(f"深度学习依赖未安装或不可用：{exc}") from exc

        with self.class_map_path.open("r", encoding="utf-8") as f:
            class_map = json.load(f)
        self._classes = [class_map[str(i)] for i in range(len(class_map))]
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        model = models.resnet50(weights=None)
        model.fc = torch.nn.Linear(model.fc.in_features, len(self._classes))
        state = torch.load(self.model_path, map_location=self._device)
        model.load_state_dict(state["model_state_dict"] if "model_state_dict" in state else state)
        model.to(self._device)
        model.eval()

        feature_model = torch.nn.Sequential(*list(model.children())[:-1])
        feature_model.to(self._device)
        feature_model.eval()

        self._transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        self._model = model
        self._feature_model = feature_model

    def predict(self, image_path: Path) -> dict[str, Any]:
        """对单张图片进行四分类预测。"""
        self._load()
        import torch

        assert self._classes is not None and self._transform is not None and self._device is not None
        image = Image.open(image_path).convert("RGB")
        tensor = self._transform(image).unsqueeze(0).to(self._device)
        with torch.no_grad():
            probs = torch.softmax(self._model(tensor), dim=1).squeeze(0).cpu().tolist()
        best_index = max(range(len(probs)), key=lambda idx: probs[idx])
        predicted_class = self._classes[best_index]
        probabilities = {cls: float(probs[idx]) for idx, cls in enumerate(self._classes)}
        return {
            "predicted_class": predicted_class,
            "category_label": CATEGORY_LABELS.get(predicted_class, predicted_class),
            "confidence": float(probs[best_index]),
            "probabilities": probabilities,
            "rationale": CLASS_RATIONALES.get(predicted_class, "系统根据图像特征给出该分类结果。"),
        }

    def extract_feature(self, image_path: Path) -> list[float]:
        """提取 2048 维深度特征，用于 Qdrant 相似检索。"""
        self._load()
        import torch

        assert self._transform is not None and self._device is not None
        image = Image.open(image_path).convert("RGB")
        tensor = self._transform(image).unsqueeze(0).to(self._device)
        with torch.no_grad():
            feature = self._feature_model(tensor).flatten().cpu().tolist()
        return [float(value) for value in feature]
