from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict
import asyncio
import httpx
import json

class AIBackend(ABC):
    """AI 后端抽象基类"""

    @abstractmethod
    async def chat_stream(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        """流式对话，返回一个异步生成器，产出文本块"""
        pass


class MockAIBackend(AIBackend):
    """用于测试的 Mock 引擎，模拟打字机效果"""
    
    async def chat_stream(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        user_msg = messages[-1].get("content", "") if messages else ""
        reply = f"（这是一条模拟回复）我收到了你的问题：“{user_msg}”。\n\n由于你还没有配置大模型 API Key，所以目前由 Mock 引擎为你服务。后续只要在设置中配置了真实的 API Key，我就能真正回答你了。"
        
        for char in reply:
            yield char
            await asyncio.sleep(0.05)


class OpenAICompatibleBackend(AIBackend):
    """兼容 OpenAI 格式的引擎"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-chat"):
        self.api_key = api_key
        # 去除末尾的斜杠
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def chat_stream(self, messages: List[Dict[str, str]]) -> AsyncIterator[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        
        url = f"{self.base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, headers=headers, json=data) as response:
                    if response.status_code != 200:
                        error_body = await response.aread()
                        error_msg = error_body.decode('utf-8', errors='ignore')
                        yield f"【API 请求被拒绝】状态码 {response.status_code}。\n返回信息：{error_msg}\n\n请检查：\n1. API Key 是否正确\n2. 模型名称是否被该平台支持\n3. 账户余额是否充足。"
                        return

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk["choices"][0]["delta"].get("content", "")
                                if delta:
                                    yield delta
                            except Exception:
                                pass
        except httpx.ConnectError as e:
            yield f"【网络连接失败】Docker 容器无法连接到 {self.base_url}。\n请检查 Base URL 是否拼写错误，或 Docker 的网络是否能够访问外网。\n错误详情：{str(e)}"
        except Exception as e:
            yield f"【未知错误】{str(e)}"