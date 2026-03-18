from fastapi import APIRouter

# 创建总路由器
router = APIRouter()

# 导入各模块路由
from app.api import users, positions, trade, portfolio, quote

# 注册路由
router.include_router(users.router, prefix="/users", tags=["用户"])
router.include_router(positions.router, prefix="/positions", tags=["持仓"])
router.include_router(trade.router, prefix="/trade", tags=["交易"])
router.include_router(portfolio.router, prefix="/portfolio", tags=["资产"])
router.include_router(quote.router, prefix="/quote", tags=["行情"])

# 后续阶段添加
# from app.api import alerts, cron
# router.include_router(alerts.router, prefix="/alerts", tags=["提醒"])
# router.include_router(cron.router, prefix="/cron-jobs", tags=["定时任务"])