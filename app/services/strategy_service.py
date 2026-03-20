"""策略服务"""

from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Strategy
from app.schemas import StrategyCreate, StrategyUpdate


class StrategyService:
    """策略服务 - 只负责 CRUD"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        data: StrategyCreate
    ) -> Strategy:
        """创建策略"""
        strategy = Strategy(
            user_id=user_id,
            stock_code=data.stock_code,
            strategy_name=data.strategy_name,
            strategy_type=data.strategy_type,
            strategy_config=data.strategy_config,
            executor_type=data.executor_type,
            executor_config=data.executor_config,
            enabled=True,
        )
        self.db.add(strategy)
        await self.db.commit()
        await self.db.refresh(strategy)
        return strategy

    async def get(self, strategy_id: int, user_id: int) -> Optional[Strategy]:
        """获取单个策略"""
        result = await self.db.execute(
            select(Strategy).where(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        user_id: int,
        stock_code: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[Strategy]:
        """获取策略列表"""
        query = select(Strategy).where(Strategy.user_id == user_id)

        if stock_code:
            query = query.where(Strategy.stock_code == stock_code)
        if enabled_only:
            query = query.where(Strategy.enabled == True)

        query = query.order_by(Strategy.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        strategy_id: int,
        user_id: int,
        data: StrategyUpdate
    ) -> Optional[Strategy]:
        """更新策略"""
        strategy = await self.get(strategy_id, user_id)
        if not strategy:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(strategy, key, value)

        await self.db.commit()
        await self.db.refresh(strategy)
        return strategy

    async def delete(self, strategy_id: int, user_id: int) -> bool:
        """删除策略"""
        strategy = await self.get(strategy_id, user_id)
        if not strategy:
            return False

        await self.db.delete(strategy)
        await self.db.commit()
        return True