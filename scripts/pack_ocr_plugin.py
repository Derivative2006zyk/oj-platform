"""
打包 OCR 插件为 .ojplugin 文件
用法：python scripts/pack_ocr_plugin.py
输出：dist/ocr_plugin.ojplugin
"""
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_PLUGIN = ROOT / "backend" / "app" / "_ocr_plugin_removed" / "ocr_plugin"
SRC_SERVICE = ROOT / "backend" / "ocr_service"
SRC_WEIGHTS = ROOT / "backend" / "ocr_service" / "weights.pth"
OUT_DIR = ROOT / "dist"
OUT_FILE = OUT_DIR / "ocr_plugin.ojplugin"
TMP = ROOT / "build" / "ocr_plugin_pack"

# 插件微服务镜像名（在宿主机上构建好，插件 compose 只用 image）
PLUGIN_IMAGE = "oj-plugin-ocr_plugin-service:0.3.0"

MANIFEST = {
    "name": "ocr_plugin",
    "display_name": "数学 OCR 拍照录题",
    "version": "0.3.0",
    "author": "OJ Team",
    "description": "基于 PaddleOCR + pix2tex 的本地离线公式识别。安装后会拉起 GPU 微服务。",
    "ui_manifest": {
        "menu_name": "拍照录题",
        "route_path": "/ocr",
        "icon": "camera",
        "order": 10,
    },
}

# 关键：不再写 build，改用 image（镜像由 pack 脚本预构建）
PLUGIN_COMPOSE = f"""\
services:
  ocr-service:
    image: {PLUGIN_IMAGE}
    container_name: oj-plugin-ocr_plugin-service
    volumes:
      - ./data/paddle_models:/root/.paddleocr
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
    networks:
      - oj-network

networks:
  oj-network:
    external: true
    name: oj-platform_default
"""


def build_service_image():
    """在宿主机上构建插件微服务镜像（避免容器内 build context 路径问题）"""
    print(f"[1/5] Building microservice image: {PLUGIN_IMAGE}")
    if not (SRC_SERVICE / "Dockerfile").exists():
        raise FileNotFoundError(f"Dockerfile not found in {SRC_SERVICE}")
    subprocess.run(
        ["docker", "build", "-t", PLUGIN_IMAGE, str(SRC_SERVICE)],
        check=True,
    )
    print(f"[1/5] Image built: {PLUGIN_IMAGE}")


def main():
    # 0. 预构建镜像
    # build_service_image()

    # 1. 清理临时目录
    print("[2/5] Preparing plugin package structure...")
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)

    # 2. manifest.json
    (TMP / "manifest.json").write_text(
        json.dumps(MANIFEST, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 3. docker-compose.yml
    (TMP / "docker-compose.yml").write_text(PLUGIN_COMPOSE, encoding="utf-8")

    # 4. backend/
    print("[3/5] Copying backend code...")
    backend_dir = TMP / "backend"
    shutil.copytree(
        SRC_PLUGIN,
        backend_dir,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    # 5. service/（仅打包源码用于留档/离线重建，不再由 compose build）
    print("[4/5] Copying service source (for archive)...")
    service_dir = TMP / "service"
    shutil.copytree(
        SRC_SERVICE,
        service_dir,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "data"),
    )
    # weights.pth 体积大（约 400MB），但已经打进 Docker 镜像了，这里不重复打包
    # 如果需要极端离线重建能力，可以取消下面两行注释
    # if SRC_WEIGHTS.exists():
    #     shutil.copy2(SRC_WEIGHTS, service_dir / "weights.pth")
    if (service_dir / "weights.pth").exists():
        (service_dir / "weights.pth").unlink()

    # 6. frontend/
    (TMP / "frontend").mkdir()
    (TMP / "frontend" / "index.html").write_text(
        "<!doctype html><html><body><h1>OCR Plugin</h1>"
        "<p>This plugin has no standalone UI.</p></body></html>",
        encoding="utf-8",
    )

    # 7. 打包
    print("[5/5] Packing .ojplugin...")
    OUT_DIR.mkdir(exist_ok=True)
    if OUT_FILE.exists():
        OUT_FILE.unlink()
    with zipfile.ZipFile(OUT_FILE, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in TMP.rglob("*"):
            if item.is_file():
                zf.write(item, item.relative_to(TMP))

    size_mb = OUT_FILE.stat().st_size / 1024 / 1024
    print(f"\n[OK] Plugin packed: {OUT_FILE} ({size_mb:.2f} MB)")
    print(f"     Image: {PLUGIN_IMAGE}")
    print(f"     Verify: docker images | findstr oj-plugin-ocr")


if __name__ == "__main__":
    main()