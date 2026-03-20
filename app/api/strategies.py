"""策略 API 路由"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.schemas import StrategyCreate, StrategyUpdate, StrategyResponse
from app.services import StrategyService
from app.auth import get_current_active_user
from app.strategies import list_strategies
from app.executors import list_executors

router = APIRouter()


@router.get("", response_model=List[StrategyResponse])
async def get_strategies(
    stock_code: Optional[str] = None,
    enabled_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取策略列表"""
    service = StrategyService(db)
    strategies = await service.list(
        user_id=current_user.id,
        stock_code=stock_code,
        enabled_only=enabled_only
    )
    return strategies


@router.post("", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    data: StrategyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建策略"""
    # 验证策略类型
    if data.strategy_type not in list_strategies():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的策略类型: {data.strategy_type}"
        )

    # 验证执行器类型
    if data.executor_type not in list_executors():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的执行器类型: {data.executor_type}"
        )

    service = StrategyService(db)
    strategy = await service.create(user_id=current_user.id, data=data)
    return strategy


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单个策略"""
    service = StrategyService(db)
    strategy = await service.get(strategy_id, current_user.id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="策略不存在"
        )
    return strategy


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int,
    data: StrategyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新策略"""
    service = StrategyService(db)
    strategy = await service.update(strategy_id, current_user.id, data)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="策略不存在"
        )
    return strategy


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除策略"""
    service = StrategyService(db)
    success = await service.delete(strategy_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="策略不存在"
        )
    return {"message": "删除成功"}


@router.get("/meta/types")
async def get_available_strategy_types():
    """获取可用的策略类型"""
    return {"strategies": list_strategies()}


@router.get("/meta/executors")
async def get_available_executor_types():
    """获取可用的执行器类型"""
    return {"executors": list_executors()}