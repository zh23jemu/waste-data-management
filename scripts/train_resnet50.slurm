#!/bin/bash
# 基于深度学习的废弃物数据管理系统 ResNet50 训练任务。
# 当前脚本按远端 Slurm 集群的 gpu 分区准备，适合正式生成论文所需模型指标。
# 提交方式示例：sbatch scripts/train_resnet50.slurm
# 如果集群要求显式账号，请把下面的账号行取消注释，并替换为 sacctmgr 中完整显示的 Account。
#SBATCH --account=gpo-ifv7xx

#SBATCH --job-name=waste-resnet50
#SBATCH --output=outputs/slurm/resnet50_%j.out
#SBATCH --error=outputs/slurm/resnet50_%j.err
#SBATCH --partition=gpu
#SBATCH --qos=normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00

set -euo pipefail

# 始终切换到提交命令所在目录，保证相对路径 data/raw、models 与本项目结构一致。
cd "${SLURM_SUBMIT_DIR}"

# 日志目录属于运行产物，已由 .gitignore 中的 outputs/ 规则忽略。
mkdir -p outputs/slurm

# 优先使用 Linux 集群常见的 .venv/bin/python；若脚本在兼容 Bash 的 Windows 环境中演练，
# 则回退到 .venv/Scripts/python.exe，始终避免使用系统 Python。
if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
elif [ -x ".venv/Scripts/python.exe" ]; then
  PYTHON_BIN=".venv/Scripts/python.exe"
else
  echo "未找到项目本地虚拟环境 Python，请先创建 .venv 并安装 requirements.txt。"
  exit 1
fi

# 输出运行环境信息，方便训练结束后在日志中确认是否真正使用了 GPU。
"${PYTHON_BIN}" - <<'PY'
import torch

print(f"CUDA 可用：{torch.cuda.is_available()}")
print(f"CUDA 设备数量：{torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"CUDA 设备名称：{torch.cuda.get_device_name(0)}")
PY

# 训练前先做轻量数据检查，避免空数据集占用集群资源。
"${PYTHON_BIN}" scripts/check_dataset.py --data-dir data/raw --min-per-class 1

# 使用项目本地虚拟环境运行训练脚本，训练结果写入 models/ 目录。
"${PYTHON_BIN}" scripts/train_resnet50.py --data-dir data/raw --output-dir models --epochs 10 --batch-size 32
