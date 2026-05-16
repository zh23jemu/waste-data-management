from __future__ import annotations

import argparse
from pathlib import Path

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
REQUIRED_CLASSES = ["hazardous", "kitchen", "other", "recyclable"]


def parse_args() -> argparse.Namespace:
    """解析数据集检查命令参数。

    默认检查项目约定的 `data/raw` 目录；如后续使用其他公开数据集整理目录，
    可以通过 `--data-dir` 指向新的四分类根目录。
    """
    parser = argparse.ArgumentParser(description="检查垃圾四分类数据集是否满足训练前置条件")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"), help="四分类图片根目录")
    parser.add_argument("--min-per-class", type=int, default=1, help="每个类别至少需要的图片数量")
    return parser.parse_args()


def count_images(data_dir: Path) -> dict[str, int]:
    """统计每个类别目录下的有效图片数量。

    只统计常见图片扩展名，避免把说明文件、下载缓存或其他临时文件误计入训练样本。
    """
    counts: dict[str, int] = {}
    for class_name in REQUIRED_CLASSES:
        class_dir = data_dir / class_name
        if not class_dir.exists():
            counts[class_name] = -1
            continue
        counts[class_name] = sum(
            1 for path in class_dir.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        )
    return counts


def main() -> None:
    """输出数据集就绪情况，并在不满足条件时以非零状态退出。

    该脚本用于训练前快速自检：先确认四个类别目录都存在，再确认每类样本数量满足最低要求。
    这样可以把“缺数据”的问题提前暴露出来，避免进入耗时训练流程后才失败。
    """
    args = parse_args()
    if args.min_per_class < 1:
        raise SystemExit("--min-per-class 必须大于等于 1。")
    if not args.data_dir.exists():
        raise SystemExit(f"数据目录不存在：{args.data_dir}")

    counts = count_images(args.data_dir)
    total = sum(count for count in counts.values() if count > 0)
    print("数据集图片统计：")
    for class_name in REQUIRED_CLASSES:
        count = counts[class_name]
        if count < 0:
            print(f"- {class_name}: 类别目录不存在")
        else:
            print(f"- {class_name}: {count} 张")
    print(f"合计：{total} 张")

    missing_dirs = [name for name, count in counts.items() if count < 0]
    insufficient = [name for name, count in counts.items() if 0 <= count < args.min_per_class]
    if missing_dirs or insufficient:
        messages = []
        if missing_dirs:
            messages.append(f"缺少类别目录：{', '.join(missing_dirs)}")
        if insufficient:
            messages.append(f"样本不足类别：{', '.join(insufficient)}")
        raise SystemExit("数据集尚未满足训练条件；" + "；".join(messages))

    print("数据集已满足当前最低检查条件，可以继续运行训练脚本。")


if __name__ == "__main__":
    main()
