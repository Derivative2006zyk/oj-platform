import pytest

from app.core.ws_manager import WSManager


class FakeWebSocket:
    """模拟 WebSocket，记录收到的消息。"""

    def __init__(self):
        self.accepted = False
        self.sent = []
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def send_json(self, data):
        if self.closed:
            raise RuntimeError("closed")
        self.sent.append(data)


@pytest.mark.asyncio
async def test_connect_and_disconnect():
    mgr = WSManager()
    ws = FakeWebSocket()

    await mgr.connect(1, ws)
    assert ws.accepted is True
    assert mgr.count(1) == 1

    mgr.disconnect(1, ws)
    assert mgr.count(1) == 0


@pytest.mark.asyncio
async def test_send_to_user():
    mgr = WSManager()
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()

    await mgr.connect(1, ws1)
    await mgr.connect(1, ws2)

    await mgr.send_to_user(1, {"type": "test"})

    assert len(ws1.sent) == 1
    assert len(ws2.sent) == 1
    assert ws1.sent[0] == {"type": "test"}


@pytest.mark.asyncio
async def test_send_to_different_users():
    mgr = WSManager()
    ws_a = FakeWebSocket()
    ws_b = FakeWebSocket()

    await mgr.connect(1, ws_a)
    await mgr.connect(2, ws_b)

    await mgr.send_to_user(1, {"hello": "alice"})

    assert len(ws_a.sent) == 1
    assert len(ws_b.sent) == 0


@pytest.mark.asyncio
async def test_disconnect_removes_key():
    mgr = WSManager()
    ws = FakeWebSocket()
    await mgr.connect(5, ws)
    assert mgr.total_connections() == 1

    mgr.disconnect(5, ws)
    assert mgr.total_connections() == 0