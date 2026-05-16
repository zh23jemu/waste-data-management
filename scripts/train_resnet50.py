from __future__ import annotations

import argparse
import json
from pathlib import Path

from sklearn.metrics import classification_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="微调 ResNet50 垃圾四分类模型")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"), help="四分类图片目录")
    parser.add_argument("--output-dir", type=Path, default=Path("models"), help="模型与指标输出目录")
    parser.add_argument("--epochs", type=int, default=10, help="训练轮次")
    parser.add_argument("--batch-size", type=int, default=16, help="批大小")
    parser.add_argument("--lr", type=float, default=1e-3, help="学习率")
    return parser.parse_args()


def main() -> None:
    """训练入口。

    使用 ImageNet 预训练 ResNet50 作为特征基础，冻结主干参数，只训练最后全连接分类层。
    这样既能降低本地算力要求，又能形成可复现实验记录。
    """
    args = parse_args()
    try:
        import torch
        from torch import nn, optim
        from torch.utils.data import DataLoader, random_split
        from torchvision import datasets, models, transforms
    except Exception as exc:
        raise SystemExit(f"训练依赖未安装，请先执行 .venv\\Scripts\\pip.exe install -r requirements.txt：{exc}")

    if not args.data_dir.exists():
        raise SystemExit(f"数据目录不存在：{args.data_dir}。请按 data/raw/recyclable 等四类目录整理公开数据集。")
    required = ["hazardous", "kitchen", "other", "recyclable"]
    missing = [name for name in required if not (args.data_dir / name).exists()]
    if missing:
        raise SystemExit(f"缺少类别目录：{', '.join(missing)}。")

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    dataset = datasets.ImageFolder(args.data_dir, transform=transform)
    total = len(dataset)
    train_len = int(total * 0.7)
    val_len = int(total * 0.15)
    test_len = total - train_len - val_len
    train_set, val_set, test_set = random_split(dataset, [train_len, val_len, test_len], generator=torch.Generator().manual_seed(42))

    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=args.batch_size)
    test_loader = DataLoader(test_set, batch_size=args.batch_size)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
    for param in model.parameters():
        param.requires_grad = False
    model.fc = nn.Linear(model.fc.in_features, len(dataset.classes))
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.fc.parameters(), lr=args.lr)
    logs = []

    def evaluate(loader: DataLoader) -> tuple[float, list[int], list[int]]:
        """评估模型并返回准确率、真实标签和预测标签。

        真实标签与预测标签会用于生成分类报告，方便后续直接写入论文“系统测试”章节。
        """
        model.eval()
        correct = 0
        count = 0
        all_labels: list[int] = []
        all_preds: list[int] = []
        with torch.no_grad():
            for images, labels in loader:
                images, labels = images.to(device), labels.to(device)
                preds = model(images).argmax(dim=1)
                correct += int((preds == labels).sum().item())
                count += int(labels.numel())
                all_labels.extend(labels.cpu().tolist())
                all_preds.extend(preds.cpu().tolist())
        return (correct / count if count else 0.0), all_labels, all_preds

    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(images), labels)
            loss.backward()
            optimizer.step()
            running_loss += float(loss.item())
        val_acc, _, _ = evaluate(val_loader)
        logs.append({"epoch": epoch, "loss": running_loss / max(len(train_loader), 1), "val_accuracy": val_acc})
        print(f"epoch={epoch} loss={logs[-1]['loss']:.4f} val_acc={val_acc:.4f}")

    test_acc, test_labels, test_preds = evaluate(test_loader)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    torch.save({"model_state_dict": model.state_dict(), "classes": dataset.classes}, args.output_dir / "resnet50_waste.pt")
    class_map = {str(index): name for index, name in enumerate(dataset.classes)}
    (args.output_dir / "class_map.json").write_text(json.dumps(class_map, ensure_ascii=False, indent=2), encoding="utf-8")
    report = classification_report(test_labels, test_preds, target_names=dataset.classes, output_dict=True, zero_division=0)
    metrics = {"classes": dataset.classes, "epochs": args.epochs, "test_accuracy": test_acc, "logs": logs, "classification_report": report}
    (args.output_dir / "training_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_dir / "classification_report.txt").write_text(
        classification_report(test_labels, test_preds, target_names=dataset.classes, zero_division=0),
        encoding="utf-8",
    )
    print(f"测试集准确率：{test_acc:.4f}")


if __name__ == "__main__":
    main()
