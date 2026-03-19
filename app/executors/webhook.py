"""Webhook通知执行器"""

from typing import Any
import httpx

from .base import Executor, ExecutionRequest, ExecutionResult


class WebhookExecutor(Executor):
    """
    Webhook通知执行器

    调用外部HTTP接口发送通知。
    适用于：对接第三方通知服务。

    config: {
        "url": "https://example.com/webhook",
        "method": "POST",  # POST 或 GET
        "headers": {},     # 可选的请求头
        "timeout": 10      # 超时时间（秒）
    }
    """

    @property
    def executor_type(self) -> str:
        return "WEBHOOK"

    async def execute(self, request: ExecutionRequest, config: dict[str, Any]) -> ExecutionResult:
        """发送Webhook通知"""
        url = config.get("url")
        if not url:
            return ExecutionResult(
                success=False,
                action="NOTIFY",
                message="Webhook URL未配置"
            )

        method = config.get("method", "POST").upper()
        headers = config.get("headers", {})
        timeout = config.get("timeout", 10)

        payload = {
            "user_id": request.user_id,
            "action": request.action,
            "stock_code": request.stock_code,
            "quantity": request.quantity,
            "price": float(request.price) if request.price else None,
            "reason": request.reason,
            "details": request.details
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

                if response.status_code < 400:
                    return ExecutionResult(
                        success=True,
                        action="NOTIFY",
                        message="Webhook调用成功",
                        details={"status_code": response.status_code}
                    )
                else:
                    return ExecutionResult(
                        success=False,
                        action="NOTIFY",
                        message=f"Webhook调用失败: HTTP {response.status_code}",
                        details={"status_code": response.status_code}
                    )
        except Exception as e:
            return ExecutionResult(
                success=False,
                action="NOTIFY",
                message=f"Webhook调用异常: {str(e)}"
            )

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