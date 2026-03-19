"""Webhook通知器"""

from typing import Any
import httpx

from .base import Notifier, NotificationMessage


class WebhookNotifier(Notifier):
    """
    Webhook通知器

    config: {
        "url": "https://example.com/webhook",
        "method": "POST",  # POST 或 GET
        "headers": {},     # 可选的请求头
        "timeout": 10      # 超时时间（秒）
    }
    """

    @property
    def notifier_type(self) -> str:
        return "WEBHOOK"

    async def send(
        self,
        user_id: int,
        message: NotificationMessage,
        config: dict[str, Any]
    ) -> bool:
        url = config.get("url")
        if not url:
            return False

        method = config.get("method", "POST").upper()
        headers = config.get("headers", {})
        timeout = config.get("timeout", 10)

        payload = {
            "user_id": user_id,
            "title": message.title,
            "content": message.content,
            "stock_code": message.stock_code,
            "alert_id": message.alert_id,
            "extra": message.extra
        }

        try:
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(
                        url,
                        params=payload,
                        headers=headers,
                        timeout=timeout
                    )
                else:
                    response = await client.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=timeout
                    )
                return response.status_code < 400
        except Exception:
            return False

    async def test_connection(self, config: dict[str, Any]) -> bool:
        """测试Webhook连接"""
        url = config.get("url")
        if not url:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.head(url, timeout=5)
                return response.status_code < 500
        except Exception:
            return False