from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.schemas import (
    PositionResponse, PositionCreate, PositionUpdate
)
from app.services import PositionService
from app.auth import get_current_active_user

router = APIRouter()


@router.get("", response_model=List[PositionResponse])
async def get_positions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取持仓列表"""
    service = PositionService(db)
    positions = await service.get_positions(current_user.id)
    return positions


@router.get("/{stock_code}", response_model=PositionResponse)
async def get_position(
    stock_code: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单只股票持仓详情"""
    service = PositionService(db)
    position = await service.get_position(current_user.id, stock_code)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未持有股票 {stock_code}"
        )
    return position


@router.post("", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(
    data: PositionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """手动创建持仓"""
    service = PositionService(db)
    try:
        position = await service.create_position(current_user.id, data)
        return position
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{stock_code}", response_model=PositionResponse)
async def update_position(
    stock_code: str,
    data: PositionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """手动调整持仓"""
    service = PositionService(db)
    try:
        position = await service.update_position(current_user.id, stock_code, data)
        return position
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{stock_code}")
async def delete_position(
    stock_code: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """清空持仓"""
    service = PositionService(db)
    try:
        await service.delete_position(current_user.id, stock_code)
        return {"message": f"已清空股票 {stock_code} 持仓"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))