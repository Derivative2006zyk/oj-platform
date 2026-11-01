# 使用带有 CUDA 12.1 和 cuDNN 8 的 Ubuntu 基础镜像
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# 设置环境变量，确保能正确找到 CUDA 库和 PyTorch 内部的 cuDNN
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    CUDA_HOME=/usr/local/cuda \
    PATH=/usr/local/cuda/bin:$PATH \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/lib/x86_64-linux-gnu:/usr/local/lib/python3.10/dist-packages/nvidia/cudnn/lib:/usr/local/lib/python3.10/dist-packages/nvidia/cublas/lib:$LD_LIBRARY_PATH

# 安装 Python 和系统依赖，并在同一层立即清理 apt 缓存
RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3-pip libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3.10 /usr/bin/python

# 升级 pip 并清理 pip 缓存
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel -i https://mirrors.aliyun.com/pypi/simple/ && \
    rm -rf /root/.cache/pip

# ===== 第1步：安装 PyTorch GPU 版本（使用国内镜像加速）=====

# 【方案A：上海交大源，推荐优先尝试】
RUN pip3 install --no-cache-dir \
    torch==2.4.1 \
    torchvision==0.19.1 \
    -f https://mirror.sjtu.edu.cn/pytorch-wheels/torch_stable.html && \
    rm -rf /root/.cache/pip

# 【方案B：清华源（若方案A失败，可切换尝试）】
# RUN pip3 install --no-cache-dir \
#     torch==2.4.1 \
#     torchvision==0.19.1 \
#     -f https://mirrors.tuna.tsinghua.edu.cn/pytorch-wheels/torch_stable.html && \
#     rm -rf /root/.cache/pip
# ===== 第2步：安装与 PaddlePaddle 兼容的 cuDNN 版本 =====
RUN pip3 install --no-cache-dir nvidia-cudnn-cu12==8.9.2.26 -i https://mirrors.aliyun.com/pypi/simple/ && \
    rm -rf /root/.cache/pip

# ===== 第3步：安装其余依赖 =====
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --extra-index-url https://www.paddlepaddle.org.cn/packages/stable/cu121/ && \
    rm -rf /root/.cache/pip /tmp/* /var/tmp/*

# 清理系统级别的无用文件，进一步压缩体积
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man

# 复制离线权重
COPY weights.pth /usr/local/lib/python3.10/dist-packages/pix2tex/model/checkpoints/weights.pth

# 复制代码 (放最后，方便改动代码时利用缓存)
COPY main.py .

EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]