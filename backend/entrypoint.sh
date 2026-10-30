#!/bin/sh
set -e

if [ "$SKIP_MIGRATIONS" != "1" ]; then
  echo "[entrypoint] waiting for database..."
  for i in $(seq 1 10); do
    if alembic upgrade head; then
      echo "[entrypoint] database migrations applied successfully."
      break
    else
      echo "[entrypoint] database not ready, retrying in 2s..."
      sleep 2
    fi
    if [ $i -eq 10 ]; then
      echo "[entrypoint] failed to apply migrations. exiting."
      exit 1
    fi
  done
fi

# ===== 检查 docker 命令可用性（Day 52 新增） =====
if command -v docker >/dev/null 2>&1; then
  echo "[entrypoint] docker CLI available: $(docker --version 2>&1 | head -1)"
else
  echo "[entrypoint] WARNING: docker CLI not found. Plugin microservices cannot be started."
fi

# ===== 检查并安装外部插件依赖 =====
if [ -d "/app/plugins_installed" ]; then
  for plugin_dir in /app/plugins_installed/*/; do
    if [ -f "${plugin_dir}backend/requirements.txt" ]; then
      echo "[entrypoint] installing dependencies for plugin: $(basename "$plugin_dir")"
      pip install --no-cache-dir -r "${plugin_dir}backend/requirements.txt" \
        -i https://pypi.tuna.tsinghua.edu.cn/simple || true
    fi
  done
fi

echo "[entrypoint] starting: $@"
exec "$@"