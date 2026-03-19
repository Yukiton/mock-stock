"""执行器抽象基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from decimal import Decimal


@dataclass
class ExecutionRequest:
    """执行请求"""
    user_id: int
    stock_code: str
    action: str  # "BUY" / "SELL" / "NOTIFY" / "HOLD"
    quantity: Optional[int] = None
    price: Optional[Decimal] = None
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    action: str
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


class Executor(ABC):
    """执行器抽象基类"""

    @property
    @abstractmethod
    def executor_type(self) -> str:
        """执行器类型标识"""
        pass

    @abstractmethod
    async def execute(self, request: ExecutionRequest, config: dict[str, Any]) -> ExecutionResult:
        """
        执行动作

        Args:
            request: 执行请求
            config: 执行器配置

        Returns:
            ExecutionResult 执行结果
        """
        pass

    async def test_connection(self, config: dict[str, Any]) -> bool:
        """
        测试执行器连接（可选实现）

        Args:
            config: 执行器配置

        Returns:
            True 表示连接正常
        """
        return True