from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event
from sqlite3 import Connection as SQLiteConnection

from app.config import settings


# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """获取数据库会话（依赖注入）"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# SQLite 外键约束启用
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection: SQLiteConnection, connection_record):
    """启用 SQLite 外键约束"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()