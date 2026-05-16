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
