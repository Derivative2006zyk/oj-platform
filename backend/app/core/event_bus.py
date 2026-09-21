import asyncio
import json
from typing import Callable, Dict, List, Awaitable, Union

from redis.asyncio import Redis, from_url

from app.core.config import settings


Handler = Union[Callable[[dict], None], Callable[[dict], Awaitable[None]]]


class EventBus:
    """
    基于 Redis Pub/Sub 的事件总线。

    用途：
    - 插件之间通过事件解耦，不直接互相调用
    - 一个插件发布事件，其他订阅了该频道的插件自动收到
    - 跨进程通信：多 backend 实例共享同一 Redis，事件全网广播

    用法：
        from app.core.event_bus import get_event_bus
        bus = get_event_bus()

        # 订阅（插件加载时）
        bus.subscribe("problem.created", on_problem_created)

        # 发布
        await bus.publish("problem.created", {"id": 123})
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis: Redis | None = None
        self._handlers: Dict[str, List[Handler]] = {}
        self._pubsub = None
        self._listener_task: asyncio.Task | None = None

    @property
    def redis(self) -> Redis:
        if self._redis is None:
            raise RuntimeError("EventBus 未连接，请先调用 connect()")
        return self._redis

    async def connect(self) -> None:
        """建立 Redis 连接并验证"""
        self._redis = from_url(
            self.redis_url, encoding="utf-8", decode_responses=True
        )
        await self._redis.ping()

    async def disconnect(self) -> None:
        """关闭连接与后台任务。

        顺序：先关 pubsub（让 listen 循环自然退出）→ 再 cancel task → 最后关 redis。
        """
        if self._pubsub:
            try:
                await self._pubsub.aclose()
            except Exception:
                pass
            self._pubsub = None

        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except (asyncio.CancelledError, Exception):
                pass
            self._listener_task = None

        if self._redis:
            try:
                await self._redis.aclose()
            except Exception:
                pass
            self._redis = None

        self._handlers.clear()

    async def publish(self, channel: str, message: dict) -> None:
        """发布一条事件到指定频道"""
        payload = json.dumps(message, ensure_ascii=False)
        await self.redis.publish(channel, payload)

    def subscribe(self, channel: str, handler: Handler) -> None:
        """
        注册事件处理器。必须在 start_listening() 之前调用。

        同一个频道可以注册多个处理器，发布时全部触发。
        """
        self._handlers.setdefault(channel, []).append(handler)

    def unsubscribe(self, channel: str, handler: Handler) -> None:
        """移除事件处理器"""
        if channel in self._handlers:
            try:
                self._handlers[channel].remove(handler)
            except ValueError:
                pass

    def clear_handlers(self) -> None:
        """清空所有本地处理器。用于测试与插件卸载（零残留卸载）。"""
        self._handlers.clear()

    async def start_listening(self) -> None:
        """启动后台监听任务。在应用启动后调用。"""
        if not self._handlers:
            # 没有订阅者，不需要启动
            return

        self._pubsub = self.redis.pubsub()
        await self._pubsub.subscribe(*self._handlers.keys())
        self._listener_task = asyncio.create_task(self._listen_loop())

    async def _listen_loop(self) -> None:
        """后台循环：接收消息，分发到处理器"""
        if self._pubsub is None:
            return

        async for message in self._pubsub.listen():
            if message.get("type") != "message":
                continue

            channel = message["channel"]
            try:
                data = json.loads(message["data"])
            except (json.JSONDecodeError, TypeError):
                data = {"raw": message.get("data")}

            for handler in list(self._handlers.get(channel, [])):
                try:
                    result = handler(data)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    # 单个 handler 出错不影响其他 handler
                    print(f"[EventBus] handler error on {channel}: {e}")

    def list_subscribed_channels(self) -> List[str]:
        """查看当前订阅的所有频道"""
        return list(self._handlers.keys())


# ===== 模块级工厂 =====
# 项目总览 9.4 约定通过 get_event_bus() 获取事件总线实例。
# 使用懒加载单例，避免 import 阶段就建立 Redis 连接。

_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """获取全局事件总线单例（懒加载）。"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus(settings.REDIS_URL)
    return _event_bus