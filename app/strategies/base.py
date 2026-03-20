"""策略抽象基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from decimal import Decimal

from .context import StrategyContext


@dataclass
class CheckResult:
    """
    策略检查结果

    所有策略统一返回此格式，直接传给执行器。
    """
    triggered: bool
    reason: Optional[str] = None
    suggested_action: str = "NOTIFY"  # "BUY" / "SELL" / "NOTIFY" / "HOLD"
    suggested_quantity: Optional[int] = None
    suggested_price: Optional[Decimal] = None
    details: dict[str, Any] = field(default_factory=dict)


class BaseStrategy(ABC):
    """策略抽象基类"""

    @property
    @abstractmethod
    def strategy_type(self) -> str:
        """策略类型标识"""
        pass

    @abstractmethod
    async def check(self, context: StrategyContext, config: dict[str, Any]) -> CheckResult:
        """
        检查是否触发（异步方法）

        Args:
            context: 包含行情、持仓、历史价格等原始数据
            config: 策略配置参数

        Returns:
            CheckResult 包含是否触发、原因、建议动作等，直接传给执行器

        Note:
            量化指标由策略器内部调用 quant 模块按需计算
        """
        pass