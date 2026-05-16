<!-- recallloom:file=rolling_summary version=1.0 lang=zh-CN -->
<!-- last-writer: [Codex] | 2026-05-16 -->
<!-- file-state: revision=5 | updated-at=2026-05-16T17:09:57+08:00 | writer-id=Codex | base-workspace-revision=8 -->

<!-- section: current_state -->
# 当前状态

本项目是“基于深度学习的废弃物数据管理系统”毕业设计工作区。当前已从资料整理进入系统原型与文档初稿并行推进阶段，目录中包含开题报告、毕业设计任务书、答辩 PPT、毕业设计手册模板、工作进程记录、中期检查报告、参考论文资料、Flask 系统源码、训练脚本、测试用例和 Markdown 版毕业设计说明书初稿。

已完成可运行 Flask 原型骨架：后端位于 waste_app/，前端位于 frontend/，训练与索引脚本位于 scripts/，测试位于 tests/。系统按任务书七个模块组织：图像识别、相似搜索、文字检索、智能交流、图片理解、历史记录和知识测试。已提供 ResNet50 推理服务封装、Qdrant 相似检索入口、DeepSeek 与星火接口封装、SQLite 历史记录、内置知识库和 20 道知识测试题；当前还补充了 scripts/check_dataset.py 数据集就绪检查脚本，并准备了 scripts/train_resnet50.slurm 作为长时间训练的 Slurm 提交脚本。

已修正开题报告、中期检查报告和工作进程记录中的旧课题或超前表述。开题报告中 MATLAB、Simulink、传感器环境感知、运动规划等旧词已清理；中期检查报告已改为系统原型、接口封装待真实密钥验证、待数据集训练等真实状态描述。

<!-- section: active_judgments -->
# 当前判断

任务书仍是后续系统开发和论文写作的主要验收依据；开题报告用于补充研究背景、意义、国内外研究现状、可行性分析和技术路线。系统应优先满足任务书中的功能与性能指标，包括四大类垃圾分类、图片上传限制、识别响应时间、相似搜索阈值、历史记录分页删除和至少 20 道知识测试题库。

当前后端基础测试已扩展到 10 项并通过，命令为 .venv\Scripts\python.exe -m pytest -q。测试覆盖健康检查、题库数量、文字检索、模型未就绪错误、非法格式上传、超过 16MB 上传限制、DeepSeek/星火缺配置错误、知识测试评分、历史记录分页删除和清空。本次复测结果仍为 10 passed；数据集检查命令 .venv\Scripts\python.exe scripts\check_dataset.py --data-dir data/raw --min-per-class 1 已正确报告四类目录均为 0 张图片。

.gitignore 当前匹配 Flask/Python/深度学习项目状态，已忽略 .venv、缓存、data/raw、data/processed、模型权重、outputs、uploads、instance 和 .env，保留 .env.example。

<!-- section: risks_open_questions -->
# 风险与未决问题

当前没有真实整理好的公开数据集、没有训练得到的模型权重、没有真实 Qdrant 千级向量索引、没有 DeepSeek 与星火真实密钥验证结果。因此不能声称模型准确率达到 90%，也不能声称相似检索耗时和真实大模型调用已经通过验收。

开题报告已生成渲染 PNG，文本问题已修正，但整体排版仍偏紧；若后续需要提交正式 DOCX，建议继续用 Word 或文档渲染流程检查页面、表格和文字遮挡。

<!-- section: next_step -->
# 下一步

下一步优先补齐真实验收证据：先向 data/raw/recyclable、data/raw/hazardous、data/raw/kitchen、data/raw/other 放入真实公开数据集图片；运行 scripts/check_dataset.py 确认四类样本就绪后，再运行 scripts/train_resnet50.py 生成 models/resnet50_waste.pt、models/class_map.json、training_metrics.json 和 classification_report.txt；启动 Qdrant 后运行 scripts/build_qdrant_index.py --image-dir data/raw --recreate；在本地 .env 配置 DeepSeek/星火密钥后实际验证接口。

完成真实训练和接口验证后，应把模型准确率、分类报告、相似检索耗时、API 调用截图或返回示例补入 docs/毕业设计说明书.md 的系统测试章节，并再转为 DOCX 进行版式检查。

<!-- section: recent_pivots -->
# 近期判断反转

- 2026-05-15：当前目录原本只有毕业设计资料，不被 RecallLoom 识别为项目根；已通过新增 README.md、AGENTS.md 和 .gitignore 将其整理为可接管的项目工作区。
- 2026-05-16：根据实际进度校准过程文档，不再把未训练模型、未配置真实密钥、未建立 Qdrant 数据的功能写成已完全验收。
