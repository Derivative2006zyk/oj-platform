# tmp_publish.py —— 临时发布脚本，测完删除

import asyncio
import sys
from app.core.event_bus import get_event_bus


async def main():
    bus = get_event_bus()
    await bus.connect()

    message = sys.argv[1] if len(sys.argv) > 1 else "hello from python"

    await bus.publish("test.channel", {"text": message})
    print(f"[发布者] 已发布到 test.channel: {message}")

    await asyncio.sleep(0.3)
    await bus.disconnect()


if __name__ == "__main__":
    asyncio.run(main())