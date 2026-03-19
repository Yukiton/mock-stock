"""通知器抽象基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class NotificationMessage:
    """通知消息"""
    title: str
    content: str
    stock_code: Optional[str] = None
    alert_id: Optional[int] = None
    extra: dict[str, Any] = None

    def __post_init__(self):
        if self.extra is None:
            self.extra = {}


class Notifier(ABC):
    """通知器抽象基类"""

    @property
    @abstractmethod
    def notifier_type(self) -> str:
        """通知器类型标识"""
        pass

    @abstractmethod
    async def send(
        self,
        user_id: int,
        message: NotificationMessage,
        config: dict[str, Any]
    ) -> bool:
        """
        发送通知

        Args:
            user_id: 目标用户ID
            message: 通知消息
            config: 通知器配置

        Returns:
            True 表示发送成功
        """
        pass

    async def test_connection(self, config: dict[str, Any]) -> bool:
        """
        测试通知器连接（可选实现）

        Args:
            config: 通知器配置

        Returns:
            True 表示连接正常
        """
        return True