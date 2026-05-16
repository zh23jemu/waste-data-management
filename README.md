# 基于深度学习的废弃物数据管理系统

本项目用于推进“基于深度学习的废弃物数据管理系统”毕业设计，包含 Flask Web 系统、ResNet50 训练/推理脚本、垃圾分类知识库、真实 DeepSeek/星火 API 接入入口，以及毕业设计说明书 Markdown 初稿。

## 功能模块

- 图像识别：上传 PNG/JPG/JPEG 图片，调用 ResNet50 四分类模型返回类别、置信度和分类依据。
- 相似搜索：基于 ResNet50 特征与 Qdrant 向量数据库检索相似案例。
- 文字检索：内置垃圾分类知识库，支持关键词查询和热门搜索建议。
- 智能交流：通过 DeepSeek API 回答垃圾分类问题。
- 图片理解：通过星火视觉接口分析图片内容并给出分类建议。
- 历史记录：SQLite 保存识别记录，支持分页、删除和清空。
- 知识测试：内置不少于 20 道题，支持随机抽题、即时反馈和得分统计。

## 环境准备

```powershell
.venv\Scripts\pip.exe install -r requirements.txt
Copy-Item .env.example .env
```

然后在 `.env` 中填写 DeepSeek 与星火 API 密钥。密钥只保存在本机 `.env`，不要提交到仓库。

## 启动系统

```powershell
.venv\Scripts\python.exe -m waste_app
```

默认访问地址为 `http://127.0.0.1:5000`。

## 模型训练

公开数据集需先整理成四分类目录：

```text
data/raw/recyclable
data/raw/hazardous
data/raw/kitchen
data/raw/other
```

执行训练：

```powershell
.venv\Scripts\python.exe scripts\train_resnet50.py --data-dir data/raw --output-dir models --epochs 10
```

训练完成后会输出模型权重、类别映射和测试指标。若模型文件不存在，系统会返回明确的模型未就绪错误，不会用假结果冒充真实识别。

## 文档

毕业设计说明书 Markdown 初稿位于 `docs/毕业设计说明书.md`，内容按任务书七个模块和技术指标组织。


## 相似搜索索引

训练模型生成 `models/resnet50_waste.pt` 和 `models/class_map.json` 后，启动 Qdrant 服务，并执行：

```powershell
.venv\Scripts\python.exe scripts\build_qdrant_index.py --image-dir data/raw --recreate
```

该脚本会扫描四分类图片目录，提取 ResNet50 深度特征，并写入 `waste_images` 集合。相似搜索接口默认只展示相似度大于 `0.65` 的结果。

## 当前状态说明

当前仓库已经具备可运行 Flask 原型、训练脚本、Qdrant 建索引脚本和论文 Markdown 初稿。真实模型准确率、Qdrant 千级向量检索性能、DeepSeek/星火真实调用结果，需要在补齐数据集和 `.env` 密钥后进一步验证，不能用模拟结果替代。
