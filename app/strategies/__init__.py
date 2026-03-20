"""策略模块"""

from .base import BaseStrategy, CheckResult
from .context import StrategyContext
from .context_builder import StrategyContextBuilder
from .threshold import ThresholdStrategy
from .ma import MAStrategy
from .macd import MACDStrategy
from .rsi import RSIStrategy
from .mcp import MCPSmartStrategy
from .registry import get_strategy, register_strategy, list_strategies

__all__ = [
    "BaseStrategy",
    "CheckResult",
    "StrategyContext",
    "StrategyContextBuilder",
    "ThresholdStrategy",
    "MAStrategy",
    "MACDStrategy",
    "RSIStrategy",
    "MCPSmartStrategy",
    "get_strategy",
    "register_strategy",
    "list_strategies",
]