import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.models import Base
from app.db.database import get_db
from app.main import create_app


# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncSession:
    """创建测试数据库会话"""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """创建测试客户端"""
    from httpx import AsyncClient, ASGITransport

    app = create_app()

    # 覆盖数据库依赖
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession):
    """创建测试用户"""
    from app.models import User
    import hashlib

    # 使用简单的 SHA256 哈希进行测试
    password_hash = hashlib.sha256("testpass123".encode()).hexdigest()
    user = User(
        username="testuser",
        password_hash=password_hash,
        balance=100000.00,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user