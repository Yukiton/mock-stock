from fastapi import APIRouter

# 创建各模块路由器
router = APIRouter()


def include_routers():
    """注册所有路由"""
    # 后续阶段添加
    # from app.api import users, positions, trade, portfolio, alerts, cron, quote
    # router.include_router(users.router, prefix="/users", tags=["用户"])
    # router.include_router(positions.router, prefix="/positions", tags=["持仓"])
    # router.include_router(trade.router, prefix="/trade", tags=["交易"])
    # router.include_router(portfolio.router, prefix="/portfolio", tags=["资产"])
    # router.include_router(alerts.router, prefix="/alerts", tags=["提醒"])
    # router.include_router(cron.router, prefix="/cron-jobs", tags=["定时任务"])
    # router.include_router(quote.router, prefix="/quote", tags=["行情"])
    pass


include_routers()