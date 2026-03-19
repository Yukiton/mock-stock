"""WebSocket通知执行器"""

from typing import Any
import json

from .base import Executor, ExecutionRequest, ExecutionResult


# 存储用户的WebSocket连接
# key: user_id, value: list of WebSocket
_user_websockets: dict[int, list] = []


def register_websocket(user_id: int, websocket) -> None:
    """注册用户的WebSocket连接"""
    if user_id not in _user_websockets:
        _user_websockets[user_id] = []
    _user_websockets[user_id].append(websocket)


def unregister_websocket(user_id: int, websocket) -> None:
    """注销用户的WebSocket连接"""
    if user_id in _user_websockets:
        if websocket in _user_websockets[user_id]:
            _user_websockets[user_id].remove(websocket)
        if not _user_websockets[user_id]:
            del _user_websockets[user_id]


class WebSocketExecutor(Executor):
    """
    WebSocket通知执行器

    通过WebSocket推送消息给用户。
    适用于：AI建议人工执行、传统量化信号提醒。

    config: {} # 无需额外配置
    """

    @property
    def executor_type(self) -> str:
        return "WEBSOCKET"

    async def execute(self, request: ExecutionRequest, config: dict[str, Any]) -> ExecutionResult:
        """发送WebSocket通知"""
        user_id = request.user_id

        if user_id not in _user_websockets:
            return ExecutionResult(
                success=False,
                action="NOTIFY",
                message=f"用户 {user_id} 没有活跃的WebSocket连接"
            )

        websockets = _user_websockets[user_id]
        if not websockets:
            return ExecutionResult(
                success=False,
                action="NOTIFY",
                message=f"用户 {user_id} 没有活跃的WebSocket连接"
            )

        payload = {
            "type": "alert",
            "action": request.action,
            "stock_code": request.stock_code,
            "quantity": request.quantity,
            "price": float(request.price) if request.price else None,
            "reason": request.reason,
            "details": request.details
        }

        success = False
        for ws in websockets[:]:  # 复制列表避免迭代时修改
            try:
                await ws.send_text(json.dumps(payload, ensure_ascii=False))
                success = True
            except Exception:
                # 连接已断开，移除
                unregister_websocket(user_id, ws)

        return ExecutionResult(
            success=success,
            action="NOTIFY",
            message="通知发送成功" if success else "通知发送失败",
            details={"sent_via": "websocket"}
        )