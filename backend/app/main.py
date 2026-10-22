from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.event_bus import get_event_bus
from app.core.plugin_registry import get_plugin_registry
from fastapi.staticfiles import StaticFiles
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ===== 启动 =====
    bus = get_event_bus()
    await bus.connect()

    registry = get_plugin_registry()
    registry.discover("app.plugins")
    await registry.load_all()

    await bus.start_listening()

    # 初始化任务队列
    from app.core.task_queue import get_task_queue
    await get_task_queue()

    print(f"[EventBus] connected to {bus.redis_url}")
    print(f"[EventBus] subscribed channels: {bus.list_subscribed_channels()}")
    print(f"[PluginRegistry] plugins: {registry.list_plugins()}")

    yield

    # ===== 关闭 =====
    from app.core.task_queue import close_task_queue
    await close_task_queue()

    registry = get_plugin_registry()
    await registry.unload_all()

    await bus.disconnect()

    print("[EventBus] disconnected")


app = FastAPI(
    title="OJ Platform",
    version="0.2.0-dev",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    bus = get_event_bus()
    redis_ok = False
    try:
        if bus._redis is not None:
            redis_ok = bool(await bus._redis.ping())
    except Exception:
        redis_ok = False

    return {
        "status": "ok",
        "redis": "ok" if redis_ok else "down",
    }


# ===== 挂载插件路由 =====
# 必须在 lifespan 之前执行，让路由在应用创建时注册。
# 但插件的实例化在 lifespan 中，所以这里先 discover 再挂载。
# 在 main.py 的末尾挂载部分修改
_registry = get_plugin_registry()
_registry.discover("app.plugins")

# 新增：扫描挂载的外部插件目录
_registry.discover_external("/app/plugins_installed")

# 触发实例化
_registry._build_instances()

# 挂载所有插件的路由
for router in _registry.collect_routers():
    app.include_router(router)

# 在 main.py 的末尾，路由挂载部分
@app.get("/api/plugins/ui")
async def get_plugins_ui():
    """获取用于前端渲染菜单的插件列表"""
    _registry = get_plugin_registry()
    return _registry.get_ui_manifests()

# ===== 挂载插件路由 =====
_registry = get_plugin_registry()
_registry.discover("app.plugins")
_registry.discover_external("/app/plugins_installed")
_registry._build_instances()

for router in _registry.collect_routers():
    app.include_router(router)

# ===== 挂载外部插件的前端静态文件 =====
# 允许前端通过 /plugins_static/插件名/frontend/index.html 访问
plugins_static_dir = "/app/plugins_installed"
if os.path.exists(plugins_static_dir):
    app.mount("/plugins_static", StaticFiles(directory=plugins_static_dir), name="plugins_static")