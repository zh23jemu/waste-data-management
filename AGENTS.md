# Codex 执行规则（少确认优化）

## 项目说明

本目录是“基于深度学习的废弃物数据管理系统”毕业设计项目工作区，当前主要包含开题报告、毕业设计任务书、答辩 PPT、模板文档和参考材料。后续代码开发、论文写作和资料整理都应围绕毕业设计任务书的模块要求与验收指标推进。

## 工作规则

- 始终使用简体中文回复。
- 文件编辑前先读取目标文件，保持最小修改，不做无关重构。
- 优先使用安全、非破坏性操作；不得执行文件删除类破坏性命令。
- Python 相关操作必须使用项目本地 `.venv`，不要使用系统 Python 或全局 pip。
- 新增代码默认包含较详细的中文注释，说明用途、关键逻辑和不明显实现细节。
- 项目发生有意义变化时，同步检查 `.gitignore` 是否仍然匹配当前内容。

## 当前毕业设计方向

系统目标是实现一个基于深度学习的废弃物数据管理系统，重点模块包括图像识别、相似搜索、文字检索、智能交流、图片理解、历史记录和知识测试。任务书要求技术栈以 Flask、PyTorch、ResNet50、Qdrant、HTML/CSS/JavaScript 为主，并支持四大类垃圾分类。

## Current Status

当前已经完成四分类数据集整理、ResNet50 远端 Slurm GPU 训练、本地 Qdrant 向量索引构建、相似检索接口验证和演示视频风格前端改造。训练数据来自 `Garbage Classification (12 classes).zip`，已整理为可回收物、有害垃圾、厨余垃圾、其他垃圾四类，共 8213 张图片。远端训练结果已经通过 GitHub Release 同步回本地 `models/` 目录，本地包含 `resnet50_waste.pt`、`class_map.json`、`classification_report.txt` 和 `training_metrics.json`。本地 Qdrant 容器使用 `http://localhost:63330` 访问，`waste_images` 集合已写入 8213 条 2048 维图片特征向量。前端已按参考视频调整为蓝色顶栏、居中内容区、统计卡、功能入口卡和模块页管理后台风格。

## Recent Changes

- 在远端 Slurm `aws` 分区使用 NVIDIA L40S 完成 ResNet50 训练，测试集准确率为 0.9830，最佳验证准确率为 0.9821。
- 已在本地安装 GitHub CLI `gh`，并通过 release 方式取回模型产物。
- 已启动本地 Qdrant 容器 `qdrant-63330`，由于 Windows 保留了 `6256-6355` 端口段，宿主机端口改用 `63330/63340` 映射容器内 `6333/6334`。
- 已运行 `.venv\Scripts\python.exe scripts\build_qdrant_index.py --image-dir data/raw --qdrant-url http://localhost:63330 --recreate`，完成 `waste_images` 集合索引构建。
- 已修复 `qdrant-client` 新版兼容问题：相似检索服务优先使用 `query_points()`，并保留旧版 `search()` 兜底。
- 已用 `battery__battery1.jpg` 验证 `/api/similar-search`：首次请求约 14.01 秒，热启动后两次约 893.19 毫秒和 891.63 毫秒，返回 1 条结果，最高相似度 1.0。
- 已运行 `.venv\Scripts\python.exe -m pytest -q`，结果为 11 passed。
- 已根据 `5c26f2b31b174502601e10d5e79ea072.mp4` 演示视频改造前端界面，覆盖首页、图像识别、相似搜索、智能搜索、智能问答、图片理解、历史记录和知识测试视图。
- 已新增 `/media/<path>` 安全图片预览路由，只允许读取 `uploads`、`data/raw` 和 `data/processed` 下的图片，用于展示上传图、历史图和相似检索图。
- `models/resnet50_waste.pt` 为较大的模型权重文件，按 `.gitignore` 规则不纳入普通 Git 提交；分类报告、类别映射和训练指标可作为说明书测试章节证据。

## Next TODO

- 将模型测试准确率、分类报告、训练环境和关键训练日志补入 `docs/毕业设计说明书.md` 的系统测试章节。
- 将 Qdrant 索引规模、相似检索耗时和返回示例补入 `docs/毕业设计说明书.md` 的系统测试章节。
- 继续人工演示检查新前端在真实上传识别、相似检索和移动端下的视觉细节。
- 补充 DeepSeek/星火真实接口调用结果。

## Open Issues

- 相似检索接口已验证，但正式说明书还未写入对应测试证据。
- 前端已按视频风格改造并通过截图检查，但真实上传演示和移动端细节仍建议再人工走一遍。
- DeepSeek 与星火接口仍待真实密钥环境验证。
- 正式 DOCX 交付前仍需做版式检查，确认图片、表格和正文不存在遮挡或拥挤。

## Architecture Decisions

- 训练任务默认使用 Slurm 集群；GPU 任务默认使用 `aws` 分区，CPU 任务默认使用 `defq` 分区，并可通过 `sbatch --partition=目标分区 脚本路径` 覆盖。
- 模型权重通过 GitHub Release 或外部制品通道同步，不直接进入普通 Git 历史。
- 项目连续性状态继续由 RecallLoom 维护，项目入口规则和当前关键状态同步记录在本文件。

<!-- RecallLoom managed bridge start -->
本项目使用 RecallLoom 管理持久化项目连续性上下文。

需要恢复项目连续性时，请优先读取：
- .recallloom/config.json
- .recallloom/update_protocol.md（先人工查看其中的项目级约束与补充说明）
- .recallloom/context_brief.md
- .recallloom/rolling_summary.md
- .recallloom/daily_logs/（如存在 active 日志，则读取其中最新的一份 active daily log）

平台入口文档负责工具行为规则；RecallLoom 负责项目连续性状态。
如果存在 update_protocol.md，请先人工查看其中的项目级约束与补充说明；v1 helper 不会自动解析其中的自然语言内容。
不要随意覆盖这些文件。
<!-- RecallLoom managed bridge end -->
