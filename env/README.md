# Idea Validation 通用环境

agentmem_lab 是新的 Idea Validation 通用 Conda 研究环境，Python 3.10；不与 Mem0、testidea、旧 .venv 或 system Python 混用。不修改、删除已有环境。

激活：

```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate agentmem_lab
which python
python --version
which pip
```

自动任务优先用绝对路径，避免非交互 shell 未加载 Conda：

```bash
~/miniconda3/bin/conda run --no-capture-output -n agentmem_lab python script.py
```

解释器必须来自 ~/miniconda3/envs/agentmem_lab/。环境历史在 agentmem_lab.yml，实际 pip 包版本在 agentmem_lab_pip_freeze.txt。重建时先按 yml 建环境，再在该环境安装 freeze 清单。只安装 numpy、pandas、scipy、matplotlib、tqdm、requests、pyyaml、pytest 及它们必要依赖；不安装 Mem0、Qdrant、torch、transformers 或 Ollama SDK。已有 Ollama 通过 127.0.0.1:11434 HTTP API 访问，模型不属于本环境。

## 安装记录

2026-10-04 创建 Python 3.10.21 环境，pip 升级检查完成。默认网络下载等待过长，确认 IPv4 HTTPS 可用后，仅中断本任务的 pip 安装进程并以进程内 IPv4 连接重试；不修改系统网络、证书验证或已有环境。
