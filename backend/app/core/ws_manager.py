from typing import Dict, Set
from fastapi import WebSocket

class WSManager:
    """WebSocket 连接管理器。"""

    def __init__(self) -> None:
        # 原有：按 user_id 维护连接（用于判题推送）
        self._connections: Dict[int, Set[WebSocket]] = {}
        # 新增：全局连接池（用于题库同步、插件状态等公共广播）
        self._global_connections: Set[WebSocket] = set()

    async def connect(self, user_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(user_id, set()).add(ws)

    def disconnect(self, user_id: int, ws: WebSocket) -> None:
        conns = self._connections.get(user_id)
        if conns is None:
            return
        conns.discard(ws)
        if not conns:
            self._connections.pop(user_id, None)

    # ===== 新增：全局连接相关 =====
    async def connect_global(self, ws: WebSocket) -> None:
        await ws.accept()
        self._global_connections.add(ws)

    def disconnect_global(self, ws: WebSocket) -> None:
        self._global_connections.discard(ws)

    async def broadcast(self, message: dict) -> None:
        """向所有全局连接广播消息"""
        for ws in list(self._global_connections):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect_global(ws)

    # ===== 原有方法保持不变 =====
    async def send_to_user(self, user_id: int, message: dict) -> None:
        conns = list(self._connections.get(user_id, set()))
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(user_id, ws)

    def count(self, user_id: int) -> int:
        return len(self._connections.get(user_id, set()))

    def total_connections(self) -> int:
        return sum(len(s) for s in self._connections.values())


_ws_manager: WSManager | None = None

def get_ws_manager() -> WSManager:
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WSManager()
    return _ws_manager