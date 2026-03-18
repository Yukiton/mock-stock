from decimal import Decimal
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Position
from app.schemas import PositionCreate, PositionUpdate


class PositionService:
    """持仓服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_positions(self, user_id: int) -> List[Position]:
        """获取用户所有持仓"""
        result = await self.db.execute(
            select(Position).where(Position.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_position(self, user_id: int, stock_code: str) -> Optional[Position]:
        """获取用户指定股票持仓"""
        result = await self.db.execute(
            select(Position).where(
                Position.user_id == user_id,
                Position.stock_code == stock_code
            )
        )
        return result.scalar_one_or_none()

    async def create_position(self, user_id: int, data: PositionCreate) -> Position:
        """创建持仓"""
        # 检查是否已存在
        existing = await self.get_position(user_id, data.stock_code)
        if existing:
            raise ValueError(f"已持有股票 {data.stock_code}，请使用更新接口")

        position = Position(
            user_id=user_id,
            stock_code=data.stock_code,
            stock_name=data.stock_name,
            quantity=data.quantity,
            avg_cost=data.avg_cost,
        )
        self.db.add(position)
        await self.db.commit()
        await self.db.refresh(position)
        return position

    async def update_position(
        self,
        user_id: int,
        stock_code: str,
        data: PositionUpdate
    ) -> Position:
        """更新持仓"""
        position = await self.get_position(user_id, stock_code)
        if not position:
            raise ValueError(f"未持有股票 {stock_code}")

        if data.stock_name is not None:
            position.stock_name = data.stock_name
        if data.quantity is not None:
            position.quantity = data.quantity
        if data.avg_cost is not None:
            position.avg_cost = data.avg_cost

        await self.db.commit()
        await self.db.refresh(position)
        return position

    async def delete_position(self, user_id: int, stock_code: str) -> bool:
        """删除持仓（清空）"""
        position = await self.get_position(user_id, stock_code)
        if not position:
            raise ValueError(f"未持有股票 {stock_code}")

        await self.db.delete(position)
        await self.db.commit()
        return True

    async def add_position(
        self,
        user_id: int,
        stock_code: str,
        stock_name: Optional[str],
        quantity: int,
        price: Decimal
    ) -> Position:
        """增加持仓（买入时调用）"""
        position = await self.get_position(user_id, stock_code)
        if position:
            # 已有持仓，更新成本和数量
            total_cost = position.avg_cost * position.quantity + price * quantity
            new_quantity = position.quantity + quantity
            position.avg_cost = total_cost / new_quantity if new_quantity > 0 else Decimal("0")
            position.quantity = new_quantity
            if stock_name:
                position.stock_name = stock_name
            await self.db.commit()
            await self.db.refresh(position)
            return position
        else:
            # 新建持仓
            position = Position(
                user_id=user_id,
                stock_code=stock_code,
                stock_name=stock_name,
                quantity=quantity,
                avg_cost=price,
            )
            self.db.add(position)
            await self.db.commit()
            await self.db.refresh(position)
            return position

    async def reduce_position(
        self,
        user_id: int,
        stock_code: str,
        quantity: int
    ) -> Position:
        """减少持仓（卖出时调用）"""
        position = await self.get_position(user_id, stock_code)
        if not position:
            raise ValueError(f"未持有股票 {stock_code}")

        if position.quantity < quantity:
            raise ValueError(f"持仓不足，当前持有 {position.quantity} 股")

        position.quantity -= quantity
        if position.quantity == 0:
            # 清空持仓，删除记录
            await self.db.delete(position)
            await self.db.commit()
            return None

        await self.db.commit()
        await self.db.refresh(position)
        return position