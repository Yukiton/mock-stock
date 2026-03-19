"""WebSocket通知器"""

from typing import Any
import asyncio
import json

from .base import Notifier, NotificationMessage


# 存储用户的WebSocket连接
# key: user_id, value: list of WebSocket
_user_websockets: dict[int, list] = {}


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


class WebSocketNotifier(Notifier):
    """
    WebSocket通知器

    config: {} # 无需额外配置
    """

    @property
    def notifier_type(self) -> str:
        return "WEBSOCKET"

    async def send(
        self,
        user_id: int,
        message: NotificationMessage,
        config: dict[str, Any]
    ) -> bool:
        if user_id not in _user_websockets:
            return False

        websockets = _user_websockets[user_id]
        if not websockets:
            return False

        payload = {
            "type": "alert",
            "title": message.title,
            "content": message.content,
            "stock_code": message.stock_code,
            "alert_id": message.alert_id,
            "extra": message.extra
        }

        success = False
        for ws in websockets[:]:  # 复制列表避免迭代时修改
            try:
                await ws.send_text(json.dumps(payload, ensure_ascii=False))
                success = True
            except Exception:
                # 连接已断开，移除
                unregister_websocket(user_id, ws)

        return success