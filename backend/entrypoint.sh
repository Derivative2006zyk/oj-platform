#!/bin/sh
set -e

if [ "$SKIP_MIGRATIONS" != "1" ]; then
  echo "[entrypoint] waiting for database..."
  # 循环重试 10 次，每次间隔 2 秒
  for i in $(seq 1 10); do
    if alembic upgrade head; then
      echo "[entrypoint] database migrations applied successfully."
      break
    else
      echo "[entrypoint] database not ready, retrying in 2s..."
      sleep 2
    fi
    
    # 如果最后一次也失败了，强行退出
    if [ $i -eq 10 ]; then
      echo "[entrypoint] failed to apply migrations after 10 attempts. exiting."
      exit 1
    fi
  done
fi

echo "[entrypoint] starting: $@"
exec "$@"