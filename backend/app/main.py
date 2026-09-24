from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.event_bus import get_event_bus
from app.core.plugin_registry import get_plugin_registry


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
_registry = get_plugin_registry()
_registry.discover("app.plugins")

# 触发实例化
_registry._build_instances()

# 挂载所有插件的路由
for router in _registry.collect_routers():
    app.include_router(router)