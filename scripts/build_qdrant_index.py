from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from qdrant_client import QdrantClient, models

from waste_app.config import Config
from waste_app.services.model_service import ModelNotReadyError, WasteClassifier

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='将参考垃圾图片批量写入 Qdrant 向量库')
    parser.add_argument('--image-dir', type=Path, default=Path('data/raw'), help='参考图片根目录，默认按四分类子目录扫描')
    parser.add_argument('--qdrant-url', default=Config.QDRANT_URL, help='Qdrant 服务地址')
    parser.add_argument('--collection', default=Config.QDRANT_COLLECTION, help='Qdrant 集合名称')
    parser.add_argument('--recreate', action='store_true', help='重建集合；会清空该集合中已有向量数据')
    parser.add_argument('--batch-size', type=int, default=64, help='批量写入大小')
    return parser.parse_args()


def iter_images(image_dir: Path):
    """遍历参考图片。

    若图片位于 `data/raw/recyclable/xxx.jpg` 这类四分类目录中，则将父目录名作为类别标签写入 payload，
    方便相似搜索结果同时展示参考图片路径和类别来源。
    """
    for path in image_dir.rglob('*'):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            yield path


def ensure_collection(client: QdrantClient, collection: str, vector_size: int, recreate: bool) -> None:
    """创建或重建 Qdrant 集合。

    ResNet50 去掉分类层后的特征维度为 2048，因此默认向量维度使用首次图片提取到的长度，
    避免代码与模型结构强绑定。相似度采用 Cosine，与任务书中相似度阈值展示方式一致。
    """
    if recreate:
        client.recreate_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )
        return
    existing = {item.name for item in client.get_collections().collections}
    if collection not in existing:
        client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )


def main() -> None:
    args = parse_args()
    image_paths = list(iter_images(args.image_dir))
    if not image_paths:
        raise SystemExit(f'未找到参考图片：{args.image_dir}。请先整理公开数据集或参考图片。')

    classifier = WasteClassifier(Config.MODEL_PATH, Config.CLASS_MAP_PATH)
    client = QdrantClient(url=args.qdrant_url)

    try:
        first_vector = classifier.extract_feature(image_paths[0])
    except ModelNotReadyError as exc:
        raise SystemExit(str(exc)) from exc

    ensure_collection(client, args.collection, len(first_vector), args.recreate)

    points: list[models.PointStruct] = []
    total = 0
    for index, image_path in enumerate(image_paths):
        vector = first_vector if index == 0 else classifier.extract_feature(image_path)
        payload = {
            'image_path': str(image_path.as_posix()),
            'category': image_path.parent.name,
            'filename': image_path.name,
        }
        points.append(models.PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL, image_path.resolve().as_posix())), vector=vector, payload=payload))
        if len(points) >= args.batch_size:
            client.upsert(collection_name=args.collection, points=points)
            total += len(points)
            print(f'已写入 {total} 条向量')
            points.clear()

    if points:
        client.upsert(collection_name=args.collection, points=points)
        total += len(points)

    print(f'Qdrant 索引构建完成：collection={args.collection}, total={total}')


if __name__ == '__main__':
    main()
