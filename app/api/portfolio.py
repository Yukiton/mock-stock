from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.services import PortfolioService
from app.auth import get_current_active_user

router = APIRouter()


@router.get("/value")
async def get_portfolio_value(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取股票持仓市值"""
    service = PortfolioService(db)
    result = await service.get_stock_value(current_user.id)
    return result


@router.get("/total")
async def get_total_assets(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取总资产（现金 + 股票市值）"""
    service = PortfolioService(db)
    result = await service.get_total_assets(current_user.id)
    return result


@router.get("/profit-loss")
async def get_profit_loss(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取持仓盈亏情况"""
    service = PortfolioService(db)
    result = await service.get_profit_loss(current_user.id)
    return result