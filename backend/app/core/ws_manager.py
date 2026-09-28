from typing import Dict, Set

from fastapi import WebSocket


class WSManager:
    """WebSocket 连接管理器。

    按 user_id 维护连接集合。同一用户可有多端连接。
    """

    def __init__(self) -> None:
        self._connections: Dict[int, Set[WebSocket]] = {}

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

    async def send_to_user(self, user_id: int, message: dict) -> None:
        """向某用户的所有连接推送消息。失败的连接被清理。"""
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
    """获取全局连接管理器单例（懒加载）。"""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WSManager()
    return _ws_manager