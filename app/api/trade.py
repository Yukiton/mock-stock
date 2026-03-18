from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.schemas import TradeRequest, TradeResponse, TransactionResponse
from app.services import TradeService
from app.auth import get_current_active_user

router = APIRouter()


@router.post("/buy", response_model=TradeResponse)
async def buy_stock(
    data: TradeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """买入股票"""
    service = TradeService(db)
    try:
        transaction = await service.buy(
            user_id=current_user.id,
            stock_code=data.stock_code,
            quantity=data.quantity,
            price=data.price,
        )
        # 获取更新后的持仓和余额
        from app.services import PositionService, UserService
        pos_service = PositionService(db)
        user_service = UserService(db)
        position = await pos_service.get_position(current_user.id, data.stock_code)
        user = await user_service.get_user(current_user.id)

        return TradeResponse(
            transaction=TransactionResponse.model_validate(transaction),
            balance=user.balance,
            position_quantity=position.quantity if position else data.quantity,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/sell", response_model=TradeResponse)
async def sell_stock(
    data: TradeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """卖出股票"""
    service = TradeService(db)
    try:
        transaction = await service.sell(
            user_id=current_user.id,
            stock_code=data.stock_code,
            quantity=data.quantity,
            price=data.price,
        )
        # 获取更新后的持仓
        from app.services import PositionService
        pos_service = PositionService(db)
        position = await pos_service.get_position(current_user.id, data.stock_code)

        # 刷新用户信息获取最新余额
        from app.services import UserService
        user_service = UserService(db)
        user = await user_service.get_user(current_user.id)

        return TradeResponse(
            transaction=TransactionResponse.model_validate(transaction),
            balance=user.balance,
            position_quantity=position.quantity if position else 0,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/history", response_model=List[TransactionResponse])
async def get_trade_history(
    stock_code: Optional[str] = Query(None, description="股票代码筛选"),
    type: Optional[str] = Query(None, description="交易类型: BUY/SELL"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取交易历史"""
    service = TradeService(db)
    transactions = await service.get_history(
        user_id=current_user.id,
        stock_code=stock_code,
        transaction_type=type,
        limit=limit,
        offset=offset,
    )
    return [TransactionResponse.model_validate(t) for t in transactions]