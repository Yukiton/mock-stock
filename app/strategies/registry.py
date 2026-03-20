"""策略注册表"""

from typing import Type

from .base import BaseStrategy
from .threshold import ThresholdStrategy
from .ma import MAStrategy
from .macd import MACDStrategy
from .rsi import RSIStrategy
from .mcp import MCPSmartStrategy


# 策略类型到类的映射
_strategy_registry: dict[str, Type[BaseStrategy]] = {
    "THRESHOLD": ThresholdStrategy,
    "MA": MAStrategy,
    "MACD": MACDStrategy,
    "RSI": RSIStrategy,
    "MCP_SMART": MCPSmartStrategy,
    "CUSTOM": None,  # 自定义策略占位
}


def get_strategy(strategy_type: str) -> BaseStrategy | None:
    """
    获取策略实例

    Args:
        strategy_type: 策略类型标识

    Returns:
        策略实例，如果不存在返回None
    """
    strategy_class = _strategy_registry.get(strategy_type)
    if strategy_class is None:
        return None
    return strategy_class()


def register_strategy(strategy_type: str, strategy_class: Type[BaseStrategy]) -> None:
    """
    注册自定义策略

    Args:
        strategy_type: 策略类型标识
        strategy_class: 策略类
    """
    _strategy_registry[strategy_type] = strategy_class


def list_strategies() -> list[str]:
    """获取所有已注册的策略类型"""
    return list(_strategy_registry.keys())