"""执行器模块"""

from .base import Executor, ExecutionRequest, ExecutionResult
from .auto_trade import AutoTradeExecutor
from .websocket import WebSocketExecutor, register_websocket, unregister_websocket
from .webhook import WebhookExecutor
from .registry import get_executor, register_executor, list_executors

__all__ = [
    "Executor",
    "ExecutionRequest",
    "ExecutionResult",
    "AutoTradeExecutor",
    "WebSocketExecutor",
    "WebhookExecutor",
    "register_websocket",
    "unregister_websocket",
    "get_executor",
    "register_executor",
    "list_executors",
]