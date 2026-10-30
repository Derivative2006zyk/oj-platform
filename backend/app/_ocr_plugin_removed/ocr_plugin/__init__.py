import asyncio
from pathlib import Path

import httpx

from app.core.plugin_base import Plugin
from app.core.plugin_registry import register_plugin

# 与插件包内 docker-compose.yml 中 container_name 保持一致
OCR_SERVICE_CONTAINER = "oj-plugin-ocr_plugin-service"
OCR_SERVICE_URL = f"http://{OCR_SERVICE_CONTAINER}:8001"
# 用 FastAPI 默认暴露的 /openapi.json 做健康探测，比自定义 /health 更通用
OCR_SERVICE_HEALTH = f"{OCR_SERVICE_URL}/openapi.json"


@register_plugin
class OcrPlugin(Plugin):
    name = "ocr_plugin"
    version = "0.3.0"
    dependencies = ["problem_plugin"]

    async def on_load(self) -> None:
        """插件加载时：仅做日志，不阻塞启动（微服务可能在安装时已经拉起）"""
        # 启动时可以顺带探测一次，但失败了也不影响主程序
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(OCR_SERVICE_HEALTH)
                if r.status_code == 200:
                    print(f"[OcrPlugin] OCR service is healthy")
                else:
                    print(f"[OcrPlugin] OCR service returned {r.status_code}")
        except Exception as e:
            print(f"[OcrPlugin] OCR service not reachable (will be retried per request): {e}")

    async def on_unload(self) -> None:
        pass

    async def on_install(self, plugin_dir: Path) -> None:
        """安装时：拉起微服务并等待健康检查通过"""
        compose_file = plugin_dir / "docker-compose.yml"
        if not compose_file.exists():
            print(f"[OcrPlugin] No docker-compose.yml found, skip microservice startup")
            return

        project_name = f"oj-plugin-{self.name}"

        print(f"[OcrPlugin] Starting microservice: project={project_name}")
        proc = await asyncio.create_subprocess_exec(
            "docker", "compose",
            "-p", project_name,
            "-f", str(compose_file),
            "up", "-d", "--build", "--wait",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            # 打印一部分日志，方便排查
            print(f"[OcrPlugin] compose up failed:\nSTDOUT:\n{stdout.decode()[-2000:]}\nSTDERR:\n{stderr.decode()[-2000:]}")
            raise RuntimeError(f"docker compose up failed with code {proc.returncode}")

        print(f"[OcrPlugin] Microservice started, waiting for health check...")

        # 保险起见，额外做一次 HTTP 层健康检查（--wait 已通过，这里只是兜底）
        for i in range(30):
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    r = await client.get(OCR_SERVICE_HEALTH)
                    if r.status_code == 200:
                        print(f"[OcrPlugin] Health check passed")
                        return
            except Exception:
                pass
            await asyncio.sleep(1)

        raise RuntimeError("OCR service health check timeout (30s)")

    async def on_uninstall(self, plugin_dir: Path) -> None:
        """卸载时：销毁微服务"""
        compose_file = plugin_dir / "docker-compose.yml"
        if not compose_file.exists():
            return

        project_name = f"oj-plugin-{self.name}"
        print(f"[OcrPlugin] Stopping microservice: project={project_name}")
        proc = await asyncio.create_subprocess_exec(
            "docker", "compose",
            "-p", project_name,
            "-f", str(compose_file),
            "down", "--remove-orphans",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f"[OcrPlugin] compose down warning: {stderr.decode()[:500]}")

    def get_routers(self):
        """返回插件路由（兼容内置 + 外部两种部署方式）"""
        try:
            # 场景 A：内置插件（app.plugins.ocr_plugin 存在，即 backend/app/plugins/ocr_plugin/ 目录在）
            from app.plugins.ocr_plugin.api import router
            from app.plugins.ocr_plugin.batch_api import router as batch_router
        except ImportError:
            # 场景 B：外部插件（从 plugins_installed/ocr_plugin/backend/ 加载）
            # 从 __init__.py 所在目录动态加载 api.py 和 batch_api.py
            import importlib.util
            import sys
            from pathlib import Path

            plugin_backend_dir = Path(__file__).parent

            # 动态加载 api.py
            api_spec = importlib.util.spec_from_file_location(
                "_ext_ocr_api", plugin_backend_dir / "api.py"
            )
            if api_spec is None or api_spec.loader is None:
                raise ImportError(f"Cannot load api.py from {plugin_backend_dir}")
            api_mod = importlib.util.module_from_spec(api_spec)
            sys.modules["_ext_ocr_api"] = api_mod
            api_spec.loader.exec_module(api_mod)
            router = api_mod.router

            # 动态加载 batch_api.py
            batch_spec = importlib.util.spec_from_file_location(
                "_ext_ocr_batch_api", plugin_backend_dir / "batch_api.py"
            )
            if batch_spec is None or batch_spec.loader is None:
                raise ImportError(f"Cannot load batch_api.py from {plugin_backend_dir}")
            batch_mod = importlib.util.module_from_spec(batch_spec)
            sys.modules["_ext_ocr_batch_api"] = batch_mod
            batch_spec.loader.exec_module(batch_mod)
            batch_router = batch_mod.router

        return [router, batch_router]