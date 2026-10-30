from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.event_bus import get_event_bus
from app.core.plugin_registry import get_plugin_registry, PLUGINS_INSTALLED_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ===== 启动 =====
    bus = get_event_bus()
    await bus.connect()

    registry = get_plugin_registry()
    registry.discover("app.plugins")
    registry.discover_external(str(PLUGINS_INSTALLED_DIR))
    registry._build_instances()
    await registry.load_all()

    await bus.start_listening()

    from app.core.task_queue import get_task_queue
    await get_task_queue()

    print(f"[EventBus] connected to {bus.redis_url}")
    print(f"[PluginRegistry] plugins: {registry.list_plugins()}")

    yield

    # ===== 关闭 =====
    from app.core.task_queue import close_task_queue
    await close_task_queue()
    await registry.unload_all()
    await bus.disconnect()


app = FastAPI(
    title="OJ Platform",
    version="0.3.0-dev",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== 全局异常捕获中间件 =====
# 防止静态资源或插件报错导致前端收到 500 并白屏
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        print(f"[Global Error] {e}")
        if request.url.path.startswith("/plugins_static"):
            return JSONResponse(status_code=404, content={"detail": "Static file error"})
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.get("/health")
async def health():
    return {"status": "ok"}


# ===== 挂载插件路由 =====
_registry = get_plugin_registry()
_registry.discover("app.plugins")
_registry.discover_external(str(PLUGINS_INSTALLED_DIR))
_registry._build_instances()

for router in _registry.collect_routers():
    app.include_router(router)


@app.get("/api/plugins/ui")
async def get_plugins_ui():
    return _registry.get_ui_manifests()


# ===== 挂载插件静态文件（最稳的原生方案） =====
plugins_static_dir = str(PLUGINS_INSTALLED_DIR)
if os.path.exists(plugins_static_dir):
    app.mount(
        "/plugins_static",
        StaticFiles(directory=plugins_static_dir),
        name="plugins_static",
    )