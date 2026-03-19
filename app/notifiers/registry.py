"""通知器注册表"""

from typing import Type

from .base import Notifier
from .websocket import WebSocketNotifier
from .webhook import WebhookNotifier
from .mcp import MCPNotifier


# 通知器类型到类的映射
_notifier_registry: dict[str, Type[Notifier]] = {
    "WEBSOCKET": WebSocketNotifier,
    "WEBHOOK": WebhookNotifier,
    "MCP": MCPNotifier,
    "SMTP": None,  # SMTP通知器待实现
}


def get_notifier(notifier_type: str) -> Notifier | None:
    """
    获取通知器实例

    Args:
        notifier_type: 通知器类型标识

    Returns:
        通知器实例，如果不存在返回None
    """
    notifier_class = _notifier_registry.get(notifier_type)
    if notifier_class is None:
        return None
    return notifier_class()


def register_notifier(notifier_type: str, notifier_class: Type[Notifier]) -> None:
    """
    注册自定义通知器

    Args:
        notifier_type: 通知器类型标识
        notifier_class: 通知器类
    """
    _notifier_registry[notifier_type] = notifier_class


def list_notifiers() -> list[str]:
    """获取所有已注册的通知器类型"""
    return list(_notifier_registry.keys())


__all__ = [
    "Notifier",
    "NotificationMessage",
    "WebSocketNotifier",
    "WebhookNotifier",
    "MCPNotifier",
    "get_notifier",
    "register_notifier",
    "list_notifiers",
]