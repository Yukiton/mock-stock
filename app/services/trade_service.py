from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Position, Transaction
from app.schemas import TradeRequest
from app.services.position_service import PositionService
from app.services.user_service import UserService


class TradeService:
    """交易服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.position_service = PositionService(db)
        self.user_service = UserService(db)

    async def buy(
        self,
        user_id: int,
        stock_code: str,
        quantity: int,
        price: Decimal,
        stock_name: Optional[str] = None
    ) -> Transaction:
        """
        买入股票

        Args:
            user_id: 用户ID
            stock_code: 股票代码
            quantity: 买入数量（股）
            price: 买入价格
            stock_name: 股票名称

        Returns:
            交易记录
        """
        # 计算交易金额
        amount = price * quantity

        # 检查余额
        user = await self.user_service.get_user(user_id)
        if not user:
            raise ValueError("用户不存在")
        if user.balance < amount:
            raise ValueError(f"余额不足，当前余额 {user.balance}，需要 {amount}")

        # 扣减余额
        await self.user_service.update_balance(user_id, -amount)

        # 增加持仓
        await self.position_service.add_position(
            user_id=user_id,
            stock_code=stock_code,
            stock_name=stock_name,
            quantity=quantity,
            price=price,
        )

        # 创建交易记录
        transaction = Transaction(
            user_id=user_id,
            stock_code=stock_code,
            stock_name=stock_name,
            type="BUY",
            quantity=quantity,
            price=price,
            amount=amount,
        )
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)

        return transaction

    async def sell(
        self,
        user_id: int,
        stock_code: str,
        quantity: int,
        price: Decimal
    ) -> Transaction:
        """
        卖出股票

        Args:
            user_id: 用户ID
            stock_code: 股票代码
            quantity: 卖出数量（股）
            price: 卖出价格

        Returns:
            交易记录
        """
        # 检查持仓
        position = await self.position_service.get_position(user_id, stock_code)
        if not position:
            raise ValueError(f"未持有股票 {stock_code}")
        if position.quantity < quantity:
            raise ValueError(f"持仓不足，当前持有 {position.quantity} 股")

        # 计算交易金额
        amount = price * quantity

        # 减少持仓
        await self.position_service.reduce_position(user_id, stock_code, quantity)

        # 增加余额
        await self.user_service.update_balance(user_id, amount)

        # 创建交易记录
        transaction = Transaction(
            user_id=user_id,
            stock_code=stock_code,
            stock_name=position.stock_name,
            type="SELL",
            quantity=quantity,
            price=price,
            amount=amount,
        )
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)

        return transaction

    async def get_history(
        self,
        user_id: int,
        stock_code: Optional[str] = None,
        transaction_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Transaction]:
        """
        获取交易历史

        Args:
            user_id: 用户ID
            stock_code: 股票代码（可选筛选）
            transaction_type: 交易类型 BUY/SELL（可选筛选）
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            交易记录列表
        """
        query = select(Transaction).where(Transaction.user_id == user_id)

        if stock_code:
            query = query.where(Transaction.stock_code == stock_code)
        if transaction_type:
            query = query.where(Transaction.type == transaction_type)

        query = query.order_by(desc(Transaction.created_at)).offset(offset).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_transaction(self, transaction_id: int, user_id: int) -> Optional[Transaction]:
        """获取单条交易记录"""
        result = await self.db.execute(
            select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.user_id == user_id
            )
        )
        return result.scalar_one_or_none()