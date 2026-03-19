"""价格提醒策略抽象基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from decimal import Decimal


@dataclass
class AlertContext:
    """
    价格提醒上下文信息

    包含大模型决策所需的全部数据：
    - 用户持仓
    - 交易记录
    - 当前行情
    - 量化指标结果
    - 相关新闻（可选）
    """
    stock_code: str
    current_price: Decimal
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    prev_close: Optional[Decimal] = None
    volume: Optional[int] = None

    # 用户持仓信息
    position_quantity: Optional[int] = None
    position_avg_cost: Optional[Decimal] = None
    position_profit_loss: Optional[Decimal] = None
    position_profit_loss_percent: Optional[Decimal] = None

    # 交易记录摘要
    recent_transactions: list[dict[str, Any]] = field(default_factory=list)

    # 量化指标结果（由量化工具计算后填入）
    indicators: dict[str, Any] = field(default_factory=dict)
    # 例如: {"ma5": 10.5, "ma10": 10.2, "macd": 0.1, "rsi": 65, ...}

    # 相关新闻（可选）
    news: list[dict[str, Any]] = field(default_factory=list)
    # 例如: [{"title": "...", "summary": "...", "sentiment": "positive"}]

    # 历史价格数据（用于量化计算）
    history_prices: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class CheckResult:
    """策略检查结果"""
    triggered: bool
    reason: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)


class AlertStrategy(ABC):
    """价格提醒策略抽象基类"""

    @property
    @abstractmethod
    def strategy_type(self) -> str:
        """策略类型标识"""
        pass

    @abstractmethod
    def check(self, context: AlertContext, config: dict[str, Any]) -> CheckResult:
        """
        检查是否触发提醒

        Args:
            context: 包含行情、持仓、交易记录、量化指标等上下文信息
            config: 策略配置参数

        Returns:
            CheckResult 包含是否触发、原因和详情
        """
        pass

    def calculate_indicators(self, context: AlertContext) -> dict[str, Any]:
        """
        计算量化指标（可选实现）

        子类可覆盖此方法以计算需要的指标

        Args:
            context: 上下文信息

        Returns:
            计算出的指标字典，会被合并到 context.indicators 中
        """
        return {}