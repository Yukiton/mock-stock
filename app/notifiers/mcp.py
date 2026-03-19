"""MCP通知器 - 通过MCP协议调用外部工具发送通知"""

from typing import Any, Optional

from .base import Notifier, NotificationMessage


class MCPNotifier(Notifier):
    """
    MCP通知器

    通过MCP协议调用外部工具发送通知。
    这允许用户通过Claude Desktop等MCP客户端接收通知。

    config: {
        "server_name": "my-mcp-server",  # MCP服务器名称
        "tool": "send_notification",      # 工具名称
        "params": {}                      # 额外参数
    }
    """

    @property
    def notifier_type(self) -> str:
        return "MCP"

    async def send(
        self,
        user_id: int,
        message: NotificationMessage,
        config: dict[str, Any]
    ) -> bool:
        """
        发送MCP通知

        注意：实际的MCP调用需要在应用层处理。
        这里返回False表示需要外部处理。

        在实际使用中，AlertService应该：
        1. 检测到notifier_type为MCP
        2. 调用MCP客户端SDK发送通知
        3. 或者将通知放入队列，由MCP服务消费
        """
        # MCP调用需要在外部处理
        # 这里只是标记需要MCP调用
        server_name = config.get("server_name")
        tool_name = config.get("tool", "send_notification")

        # 记录需要发送的通知（可由MCP服务轮询）
        await self._queue_mcp_notification(
            user_id=user_id,
            message=message,
            server_name=server_name,
            tool_name=tool_name,
            params=config.get("params", {})
        )

        return True

    async def _queue_mcp_notification(
        self,
        user_id: int,
        message: NotificationMessage,
        server_name: str,
        tool_name: str,
        params: dict
    ) -> None:
        """
        将MCP通知加入队列

        实际实现可以：
        1. 写入数据库队列表
        2. 写入Redis队列
        3. 调用MCP客户端SDK

        这里提供一个简单的内存队列实现
        """
        global _mcp_queue
        from datetime import datetime

        notification = {
            "user_id": user_id,
            "title": message.title,
            "content": message.content,
            "stock_code": message.stock_code,
            "alert_id": message.alert_id,
            "server_name": server_name,
            "tool_name": tool_name,
            "params": params,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }

        # 加入待发送队列
        _mcp_queue.append(notification)

        # 限制队列大小
        if len(_mcp_queue) > 1000:
            # 移除最旧的已发送通知
            _mcp_queue = [n for n in _mcp_queue if n["status"] == "pending"][-500:]


# MCP通知队列（内存实现，生产环境应使用Redis或数据库）
_mcp_queue: list[dict] = []


def get_pending_mcp_notifications(user_id: Optional[int] = None) -> list[dict]:
    """获取待发送的MCP通知"""
    if user_id is not None:
        return [n for n in _mcp_queue if n["user_id"] == user_id and n["status"] == "pending"]
    return [n for n in _mcp_queue if n["status"] == "pending"]


def mark_mcp_notification_sent(notification_id: int) -> None:
    """标记MCP通知已发送"""
    for n in _mcp_queue:
        if id(n) == notification_id:
            n["status"] = "sent"
            break