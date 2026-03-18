from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Base
from app.db.database import engine


async def init_db():
    """初始化数据库（创建所有表）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """删除所有表（用于测试）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)