FROM python:3.11-slim

WORKDIR /workspace

# 沙箱镜像不含网络工具、编译器等，保持最小
# 用户代码通过 bind mount 挂载到 /workspace/main.py

CMD ["python", "/workspace/main.py"]