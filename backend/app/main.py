from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.event_bus import get_event_bus
from app.plugins.problem_plugin.api import router as problem_router
from app.plugins.problem_plugin.image_api import router as image_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    bus = get_event_bus()

    # ===== 启动 =====
    await bus.connect()
    # 各插件加载时会调用 bus.subscribe 注册处理器
    # 所有插件加载完成后，启动监听
    await bus.start_listening()
    print(f"[EventBus] connected to {bus.redis_url}")
    print(f"[EventBus] subscribed channels: {bus.list_subscribed_channels()}")

    yield

    # ===== 关闭 =====
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

app.include_router(problem_router)
app.include_router(image_router)


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