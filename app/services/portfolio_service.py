from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Position, User
from app.quote import get_quote_provider, StockQuote


class PortfolioService:
    """资产估值服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_positions_with_value(self, user_id: int) -> List[dict]:
        """
        获取持仓列表及市值

        Args:
            user_id: 用户ID

        Returns:
            持仓列表，包含当前价格和市值
        """
        result = await self.db.execute(
            select(Position).where(Position.user_id == user_id)
        )
        positions = result.scalars().all()

        quote_provider = get_quote_provider()
        positions_with_value = []

        for pos in positions:
            quote = quote_provider.get_quote(pos.stock_code)
            current_price = quote.current_price if quote else None
            market_value = None
            profit_loss = None
            profit_loss_percent = None

            if current_price is not None and pos.quantity > 0:
                market_value = current_price * pos.quantity
                if pos.avg_cost > 0:
                    cost = pos.avg_cost * pos.quantity
                    profit_loss = market_value - cost
                    profit_loss_percent = (profit_loss / cost) * 100

            positions_with_value.append({
                "stock_code": pos.stock_code,
                "stock_name": pos.stock_name,
                "quantity": pos.quantity,
                "avg_cost": pos.avg_cost,
                "current_price": current_price,
                "market_value": market_value,
                "profit_loss": profit_loss,
                "profit_loss_percent": profit_loss_percent,
            })

        return positions_with_value

    async def get_stock_value(self, user_id: int) -> dict:
        """
        获取股票持仓总市值

        Args:
            user_id: 用户ID

        Returns:
            包含各股票市值和总市值的字典
        """
        positions_with_value = await self.get_positions_with_value(user_id)

        total_value = Decimal("0")
        items = []

        for pos in positions_with_value:
            market_value = pos["market_value"] or Decimal("0")
            total_value += market_value
            items.append({
                "stock_code": pos["stock_code"],
                "stock_name": pos["stock_name"],
                "quantity": pos["quantity"],
                "current_price": pos["current_price"],
                "market_value": market_value,
            })

        return {
            "items": items,
            "total_value": total_value,
        }

    async def get_total_assets(self, user_id: int) -> dict:
        """
        获取总资产（现金 + 股票市值）

        Args:
            user_id: 用户ID

        Returns:
            总资产信息
        """
        # 获取现金余额
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("用户不存在")

        cash_balance = user.balance

        # 获取股票市值
        stock_info = await self.get_stock_value(user_id)
        stock_value = stock_info["total_value"]

        total_value = cash_balance + stock_value

        return {
            "cash_balance": cash_balance,
            "stock_value": stock_value,
            "total_value": total_value,
        }

    async def get_profit_loss(self, user_id: int) -> dict:
        """
        获取持仓盈亏情况

        Args:
            user_id: 用户ID

        Returns:
            盈亏信息
        """
        positions_with_value = await self.get_positions_with_value(user_id)

        total_cost = Decimal("0")
        total_market_value = Decimal("0")
        items = []

        for pos in positions_with_value:
            if pos["quantity"] > 0:
                cost = pos["avg_cost"] * pos["quantity"]
                market_value = pos["market_value"] or Decimal("0")

                total_cost += cost
                total_market_value += market_value

                items.append({
                    "stock_code": pos["stock_code"],
                    "stock_name": pos["stock_name"],
                    "quantity": pos["quantity"],
                    "avg_cost": pos["avg_cost"],
                    "current_price": pos["current_price"],
                    "profit_loss": pos["profit_loss"],
                    "profit_loss_percent": pos["profit_loss_percent"],
                })

        total_profit_loss = total_market_value - total_cost
        total_profit_loss_percent = (
            (total_profit_loss / total_cost) * 100 if total_cost > 0 else None
        )

        return {
            "items": items,
            "total_cost": total_cost,
            "total_market_value": total_market_value,
            "total_profit_loss": total_profit_loss,
            "total_profit_loss_percent": total_profit_loss_percent,
        }