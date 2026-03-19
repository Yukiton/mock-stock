"""自动交易执行器 - 自动调用交易API完成买入/卖出"""

from typing import Any
from decimal import Decimal

from .base import Executor, ExecutionRequest, ExecutionResult


class AutoTradeExecutor(Executor):
    """
    自动交易执行器

    收到触发后自动调用交易API完成买入/卖出。
    适用于：AI自动模拟交易、传统量化自动交易。

    config: {
        "dry_run": false,  # 是否模拟运行（不实际交易）
        "max_quantity": 1000  # 单次最大交易数量
    }
    """

    @property
    def executor_type(self) -> str:
        return "AUTO_TRADE"

    async def execute(self, request: ExecutionRequest, config: dict[str, Any]) -> ExecutionResult:
        """
        执行交易

        注意：实际交易需要调用TradeService，这里返回执行请求，
        由AlertService处理实际的交易调用。
        """
        if request.action not in ("BUY", "SELL"):
            return ExecutionResult(
                success=False,
                action=request.action,
                message=f"自动交易执行器不支持动作: {request.action}"
            )

        dry_run = config.get("dry_run", False)
        max_quantity = config.get("max_quantity", 10000)

        # 检查数量限制
        if request.quantity and request.quantity > max_quantity:
            return ExecutionResult(
                success=False,
                action=request.action,
                message=f"交易数量 {request.quantity} 超过最大限制 {max_quantity}"
            )

        # 返回执行请求，由AlertService处理
        return ExecutionResult(
            success=True,
            action=request.action,
            message=f"{'[模拟] ' if dry_run else ''}准备执行{request.action}",
            details={
                "stock_code": request.stock_code,
                "quantity": request.quantity,
                "price": float(request.price) if request.price else None,
                "reason": request.reason,
                "dry_run": dry_run,
                "requires_trade": True,  # 标记需要执行交易
            }
        )