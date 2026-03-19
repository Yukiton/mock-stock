"""执行器注册表"""

from typing import Type

from .base import Executor, ExecutionRequest, ExecutionResult
from .auto_trade import AutoTradeExecutor
from .websocket import WebSocketExecutor
from .webhook import WebhookExecutor


# 执行器类型到类的映射
_executor_registry: dict[str, Type[Executor]] = {
    "AUTO_TRADE": AutoTradeExecutor,
    "WEBSOCKET": WebSocketExecutor,
    "WEBHOOK": WebhookExecutor,
}


def get_executor(executor_type: str) -> Executor | None:
    """
    获取执行器实例

    Args:
        executor_type: 执行器类型标识

    Returns:
        执行器实例，如果不存在返回None
    """
    executor_class = _executor_registry.get(executor_type)
    if executor_class is None:
        return None
    return executor_class()


def register_executor(executor_type: str, executor_class: Type[Executor]) -> None:
    """
    注册自定义执行器

    Args:
        executor_type: 执行器类型标识
        executor_class: 执行器类
    """
    _executor_registry[executor_type] = executor_class


def list_executors() -> list[str]:
    """获取所有已注册的执行器类型"""
    return list(_executor_registry.keys())


__all__ = [
    "Executor",
    "ExecutionRequest",
    "ExecutionResult",
    "AutoTradeExecutor",
    "WebSocketExecutor",
    "WebhookExecutor",
    "get_executor",
    "register_executor",
    "list_executors",
]