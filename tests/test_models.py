"""数据库模型测试"""
import pytest
from sqlalchemy import select
from decimal import Decimal

from app.models import User, Position, Transaction, Strategy, CronJob


@pytest.mark.asyncio
async def test_create_user(db_session):
    """测试创建用户"""
    user = User(
        username="newuser",
        password_hash="hashed_password",
        balance=Decimal("10000.00"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.username == "newuser"
    assert user.balance == Decimal("10000.00")
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_create_position(db_session, test_user):
    """测试创建持仓"""
    position = Position(
        user_id=test_user.id,
        stock_code="000001",
        stock_name="平安银行",
        quantity=1000,
        avg_cost=Decimal("15.50"),
    )
    db_session.add(position)
    await db_session.commit()
    await db_session.refresh(position)

    assert position.id is not None
    assert position.user_id == test_user.id
    assert position.stock_code == "000001"
    assert position.quantity == 1000


@pytest.mark.asyncio
async def test_create_transaction(db_session, test_user):
    """测试创建交易记录"""
    transaction = Transaction(
        user_id=test_user.id,
        stock_code="000001",
        stock_name="平安银行",
        type="BUY",
        quantity=100,
        price=Decimal("15.50"),
        amount=Decimal("1550.00"),
    )
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)

    assert transaction.id is not None
    assert transaction.type == "BUY"
    assert transaction.amount == Decimal("1550.00")


@pytest.mark.asyncio
async def test_create_strategy(db_session, test_user):
    """测试创建策略"""
    strategy = Strategy(
        user_id=test_user.id,
        stock_code="000001",
        strategy_name="突破20元策略",
        strategy_type="THRESHOLD",
        strategy_config={"upper": 20.0, "lower": 10.0},
        executor_type="WEBSOCKET",
        executor_config={},
    )
    db_session.add(strategy)
    await db_session.commit()
    await db_session.refresh(strategy)

    assert strategy.id is not None
    assert strategy.strategy_type == "THRESHOLD"
    assert strategy.enabled is True


@pytest.mark.asyncio
async def test_create_cron_job(db_session):
    """测试创建定时任务"""
    job = CronJob(
        name="每日价格检查",
        cron_expression="0 9 * * 1-5",
        job_type="PRICE_CHECK",
        config={"stocks": ["000001", "000002"]},
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    assert job.id is not None
    assert job.name == "每日价格检查"
    assert job.enabled is True


@pytest.mark.asyncio
async def test_user_position_relationship(db_session, test_user):
    """测试用户持仓关联"""
    position1 = Position(
        user_id=test_user.id,
        stock_code="000001",
        quantity=100,
        avg_cost=Decimal("15.00"),
    )
    position2 = Position(
        user_id=test_user.id,
        stock_code="000002",
        quantity=200,
        avg_cost=Decimal("20.00"),
    )
    db_session.add_all([position1, position2])
    await db_session.commit()

    # 使用显式查询验证持仓数量
    result = await db_session.execute(
        select(Position).where(Position.user_id == test_user.id)
    )
    positions = result.scalars().all()
    assert len(positions) == 2


@pytest.mark.asyncio
async def test_user_cascade_delete(db_session):
    """测试用户删除时级联删除持仓和交易"""
    import hashlib

    # 使用简单的 SHA256 哈希进行测试
    password_hash = hashlib.sha256("password".encode()).hexdigest()

    user = User(
        username="delete_test",
        password_hash=password_hash,
        balance=10000,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 创建持仓
    position = Position(
        user_id=user.id,
        stock_code="000001",
        quantity=100,
    )
    db_session.add(position)
    await db_session.commit()

    # 删除用户
    await db_session.delete(user)
    await db_session.commit()

    # 验证持仓也被删除
    result = await db_session.execute(
        select(Position).where(Position.user_id == user.id)
    )
    positions = result.scalars().all()
    assert len(positions) == 0