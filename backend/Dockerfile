FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置时区（可选，避免时间戳偏差）
ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED=1

# 替换 Debian 软件源为清华镜像，解决 apt 下载卡死的问题
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖清单，利用 Docker 层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目代码
COPY . .

# 创建上传目录
RUN mkdir -p /app/uploads

# 从官方镜像拷贝 docker CLI，worker 判题调用沙箱时使用
COPY --from=docker:27-cli /usr/local/bin/docker /usr/local/bin/docker

# 【Day 52 新增】Docker Compose 插件，供插件微服务编排（on_install/on_uninstall）
COPY docker-compose-linux /usr/local/libexec/docker/cli-plugins/docker-compose
RUN chmod +x /usr/local/libexec/docker/cli-plugins/docker-compose \
    && rm -f /app/docker-compose-linux

# 暴露端口
EXPOSE 8000

# 让 entrypoint.sh 可执行
RUN chmod +x /app/entrypoint.sh

# 启动：先跑迁移，再执行 CMD（默认为启动后端 API）
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]