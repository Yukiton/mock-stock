from decimal import Decimal
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas import UserCreate, UserResponse, BalanceUpdate
from app.auth import get_password_hash, verify_password


class UserService:
    """用户服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        """创建用户"""
        # 检查用户名是否已存在
        result = await self.db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise ValueError(f"用户名 '{user_data.username}' 已存在")

        user = User(
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            balance=Decimal("0.00"),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """验证用户"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    async def get_user(self, user_id: int) -> Optional[User]:
        """获取用户"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def update_balance(self, user_id: int, amount: Decimal) -> User:
        """更新用户余额"""
        user = await self.get_user(user_id)
        if not user:
            raise ValueError("用户不存在")

        new_balance = user.balance + amount
        if new_balance < 0:
            raise ValueError("余额不足")

        user.balance = new_balance
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def set_balance(self, user_id: int, balance: Decimal) -> User:
        """设置用户余额（直接设置）"""
        user = await self.get_user(user_id)
        if not user:
            raise ValueError("用户不存在")

        if balance < 0:
            raise ValueError("余额不能为负数")

        user.balance = balance
        await self.db.commit()
        await self.db.refresh(user)
        return user