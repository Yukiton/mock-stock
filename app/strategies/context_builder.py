"""策略上下文构建器"""

from decimal import Decimal
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Position, Transaction
from app.strategies.context import StrategyContext
from app.quote import get_quote_provider


class StrategyContextBuilder:
    """
    策略上下文构建器

    职责：拉取数据构建 StrategyContext
    - 行情数据（quote_provider）
    - 持仓信息（db）
    - 历史价格（akshare）
    - 交易记录（db）

    不计算量化指标，由策略器内部按需调用 quant 模块。
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def build(self, user_id: int, stock_code: str) -> StrategyContext:
        """
        构建策略上下文

        Args:
            user_id: 用户ID
            stock_code: 股票代码

        Returns:
            StrategyContext 策略执行上下文
        """
        context = StrategyContext(
            user_id=user_id,
            stock_code=stock_code,
            current_price=Decimal("0")
        )

        # 拉取行情
        await self._fetch_quote(context)

        # 拉取持仓
        await self._fetch_position(context)

        # 拉取交易记录
        await self._fetch_recent_transactions(context)

        # 拉取历史价格
        await self._fetch_history_prices(context)

        return context

    async def _fetch_quote(self, context: StrategyContext) -> None:
        """拉取行情数据"""
        provider = get_quote_provider()
        quote = provider.get_quote(context.stock_code)
        if quote:
            context.current_price = quote.current_price or Decimal("0")
            context.open_price = quote.open_price
            context.high_price = quote.high_price
            context.low_price = quote.low_price
            context.prev_close = quote.prev_close
            context.volume = quote.volume

    async def _fetch_position(self, context: StrategyContext) -> None:
        """拉取持仓信息"""
        result = await self.db.execute(
            select(Position).where(
                Position.user_id == context.user_id,
                Position.stock_code == context.stock_code
            )
        )
        position = result.scalar_one_or_none()

        if position:
            context.position_quantity = position.quantity
            context.position_avg_cost = position.avg_cost

            # 计算盈亏
            if context.current_price and position.avg_cost:
                profit = (context.current_price - position.avg_cost) * position.quantity
                profit_percent = ((context.current_price - position.avg_cost) / position.avg_cost) * 100
                context.position_profit_loss = profit
                context.position_profit_loss_percent = profit_percent

    async def _fetch_recent_transactions(self, context: StrategyContext, limit: int = 5) -> None:
        """拉取最近交易记录"""
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.user_id == context.user_id, Transaction.stock_code == context.stock_code)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        transactions = result.scalars().all()

        context.recent_transactions = [
            {
                "type": t.type,
                "quantity": t.quantity,
                "price": str(t.price),
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in transactions
        ]

    async def _fetch_history_prices(self, context: StrategyContext, limit: int = 60) -> None:
        """
        拉取历史价格数据

        使用 akshare 获取历史 K 线数据
        """
        try:
            import akshare as ak

            stock_code = context.stock_code

            # 判断市场
            if stock_code.startswith(('5', '6', '9')):
                market = "sh"
            else:
                market = "sz"

            symbol = f"{market}{stock_code}"

            # 获取历史数据
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                adjust=""  # 不复权
            )

            if df is None or df.empty:
                return

            # 转换为列表（从新到旧）
            prices = []
            for _, row in df.iloc[-limit:].iterrows():
                prices.append({
                    "date": str(row.iloc[0]) if len(row) > 0 else None,
                    "open": float(row.iloc[1]) if len(row) > 1 else None,
                    "close": float(row.iloc[2]) if len(row) > 2 else None,
                    "high": float(row.iloc[3]) if len(row) > 3 else None,
                    "low": float(row.iloc[4]) if len(row) > 4 else None,
                    "volume": float(row.iloc[5]) if len(row) > 5 else None,
                    "amount": float(row.iloc[6]) if len(row) > 6 else None,
                })

            # 反转为从新到旧
            context.history_prices = list(reversed(prices))

        except Exception:
            context.history_prices = []