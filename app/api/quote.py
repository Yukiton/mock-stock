from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query

from app.quote import get_quote_provider, StockQuote
from app.auth import get_current_active_user
from app.models import User

router = APIRouter()


@router.get("/batch")
async def get_batch_quotes(
    codes: str = Query(..., description="股票代码列表，逗号分隔"),
    current_user: User = Depends(get_current_active_user)
):
    """批量获取股票行情"""
    stock_codes = [code.strip() for code in codes.split(",") if code.strip()]
    if not stock_codes:
        raise HTTPException(status_code=400, detail="请提供股票代码")

    provider = get_quote_provider()
    quotes = provider.get_quotes(stock_codes)
    return quotes


@router.get("/{stock_code}")
async def get_stock_quote(
    stock_code: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取单只股票实时行情"""
    provider = get_quote_provider()
    quote = provider.get_quote(stock_code)
    if not quote:
        raise HTTPException(status_code=404, detail=f"无法获取股票 {stock_code} 的行情")
    return quote