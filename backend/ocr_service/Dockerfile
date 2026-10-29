# 使用带有 CUDA 12.1 和 cuDNN 的 Ubuntu 基础镜像
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# 设置环境变量，确保能正确找到 CUDA 库
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    CUDA_HOME=/usr/local/cuda \
    PATH=/usr/local/cuda/bin:$PATH \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/lib/x86_64-linux-gnu:/usr/local/lib/python3.10/dist-packages/nvidia/cudnn/lib:/usr/local/lib/python3.10/dist-packages/nvidia/cublas/lib:$LD_LIBRARY_PATH

# 安装 Python 和系统依赖
RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3-pip libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3.10 /usr/bin/python

# 升级 pip 等构建工具
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel -i https://mirrors.aliyun.com/pypi/simple/

# ===== 第1步：从 PyTorch 官方源安装 GPU 版本 =====
RUN pip3 install --no-cache-dir \
    torch==2.4.1 \
    torchvision==0.19.1 \
    --index-url https://download.pytorch.org/whl/cu121

# 复制剩余的依赖清单
COPY requirements.txt .

# ===== 第2步：安装剩余依赖（为 paddlepaddle-gpu 指定官方源） =====
RUN pip3 install --no-cache-dir -r requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --extra-index-url https://www.paddlepaddle.org.cn/packages/stable/cu121/
# 复制离线权重
COPY weights.pth /usr/local/lib/python3.10/dist-packages/pix2tex/model/checkpoints/weights.pth

COPY main.py .

EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]