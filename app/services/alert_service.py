"""价格提醒服务"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PriceAlert, Position, Transaction
from app.strategies import (
    AlertContext,
    CheckResult,
    get_strategy,
)
from app.executors import (
    ExecutionRequest,
    ExecutionResult,
    get_executor,
)
from app.quote import get_quote_provider
from app.schemas import AlertCreate, AlertUpdate
from app.quant import calculate_all_indicators


class AlertService:
    """价格提醒服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_alert(
        self,
        user_id: int,
        data: AlertCreate
    ) -> PriceAlert:
        """创建价格提醒"""
        alert = PriceAlert(
            user_id=user_id,
            stock_code=data.stock_code,
            alert_name=data.alert_name,
            strategy_type=data.strategy_type,
            strategy_config=data.strategy_config,
            executor_type=data.executor_type,
            executor_config=data.executor_config,
            enabled=True,
        )
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def get_alert(self, alert_id: int, user_id: int) -> Optional[PriceAlert]:
        """获取单个提醒"""
        result = await self.db.execute(
            select(PriceAlert).where(
                PriceAlert.id == alert_id,
                PriceAlert.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_alerts(
        self,
        user_id: int,
        stock_code: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[PriceAlert]:
        """获取提醒列表"""
        query = select(PriceAlert).where(PriceAlert.user_id == user_id)

        if stock_code:
            query = query.where(PriceAlert.stock_code == stock_code)
        if enabled_only:
            query = query.where(PriceAlert.enabled == True)

        query = query.order_by(PriceAlert.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_alert(
        self,
        alert_id: int,
        user_id: int,
        data: AlertUpdate
    ) -> Optional[PriceAlert]:
        """更新提醒"""
        alert = await self.get_alert(alert_id, user_id)
        if not alert:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(alert, key, value)

        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def delete_alert(self, alert_id: int, user_id: int) -> bool:
        """删除提醒"""
        alert = await self.get_alert(alert_id, user_id)
        if not alert:
            return False

        await self.db.delete(alert)
        await self.db.commit()
        return True

    async def check_alert(self, alert: PriceAlert) -> CheckResult:
        """
        检查单个提醒是否触发

        构建上下文并执行策略检查，返回最终决策。
        """
        strategy = get_strategy(alert.strategy_type)
        if not strategy:
            return CheckResult(triggered=False, reason=f"未知策略类型: {alert.strategy_type}")

        # 构建上下文
        context = await self._build_context(alert.user_id, alert.stock_code)

        # 执行策略检查（异步）
        result = await strategy.check(context, alert.strategy_config)

        return result

    async def trigger_alert(
        self,
        alert: PriceAlert,
        check_result: CheckResult
    ) -> ExecutionResult:
        """
        触发提醒，执行动作
        """
        executor = get_executor(alert.executor_type)
        if not executor:
            return ExecutionResult(
                success=False,
                action="NONE",
                message=f"未知的执行器类型: {alert.executor_type}"
            )

        # 使用 CheckResult 的建议动作
        action = check_result.suggested_action
        if action not in ("BUY", "SELL"):
            action = "NOTIFY"

        # 构建执行请求
        request = ExecutionRequest(
            user_id=alert.user_id,
            stock_code=alert.stock_code,
            action=action,
            quantity=check_result.suggested_quantity,
            price=check_result.suggested_price,
            reason=check_result.reason or "条件已触发",
            details=check_result.details
        )

        # 执行
        result = await executor.execute(request, alert.executor_config or {})

        # 如果是自动交易执行器，需要实际执行交易
        if result.success and result.details.get("requires_trade"):
            trade_result = await self._execute_trade(alert, request, result.details.get("dry_run", False))
            result = trade_result

        # 更新最后触发时间
        if result.success:
            alert.last_triggered_at = datetime.now(timezone.utc)
            await self.db.commit()

        return result

    async def _execute_trade(
        self,
        alert: PriceAlert,
        request: ExecutionRequest,
        dry_run: bool = False
    ) -> ExecutionResult:
        """
        执行实际交易
        """
        if dry_run:
            return ExecutionResult(
                success=True,
                action=request.action,
                message=f"[模拟] {request.action} 成功",
                details={
                    "stock_code": request.stock_code,
                    "quantity": request.quantity,
                    "price": float(request.price) if request.price else None
                }
            )

        # 实际交易逻辑
        from app.services import TradeService

        try:
            trade_service = TradeService(self.db)

            # 获取当前价格（如果没有指定）
            price = request.price
            if not price:
                provider = get_quote_provider()
                quote = provider.get_quote(request.stock_code)
                if quote and quote.current_price:
                    price = quote.current_price
                else:
                    return ExecutionResult(
                        success=False,
                        action=request.action,
                        message="无法获取当前价格"
                    )

            if request.action == "BUY":
                transaction = await trade_service.buy(
                    user_id=request.user_id,
                    stock_code=request.stock_code,
                    quantity=request.quantity or 100,
                    price=price
                )
            else:  # SELL
                transaction = await trade_service.sell(
                    user_id=request.user_id,
                    stock_code=request.stock_code,
                    quantity=request.quantity or 100,
                    price=price
                )

            return ExecutionResult(
                success=True,
                action=request.action,
                message=f"{request.action} 成功",
                details={
                    "transaction_id": transaction.id,
                    "stock_code": request.stock_code,
                    "quantity": transaction.quantity,
                    "price": float(transaction.price)
                }
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                action=request.action,
                message=f"交易执行失败: {str(e)}"
            )

    async def check_all_alerts(self, user_id: Optional[int] = None) -> List[dict]:
        """
        检查所有启用的提醒

        Args:
            user_id: 可选，只检查指定用户的提醒

        Returns:
            触发的提醒列表
        """
        query = select(PriceAlert).where(PriceAlert.enabled == True)
        if user_id:
            query = query.where(PriceAlert.user_id == user_id)

        result = await self.db.execute(query)
        alerts = result.scalars().all()

        triggered = []
        for alert in alerts:
            try:
                check_result = await self.check_alert(alert)

                if check_result.triggered:
                    exec_result = await self.trigger_alert(alert, check_result)
                    triggered.append({
                        "alert_id": alert.id,
                        "stock_code": alert.stock_code,
                        "reason": check_result.reason,
                        "action": exec_result.action,
                        "success": exec_result.success,
                        "message": exec_result.message
                    })
            except Exception as e:
                triggered.append({
                    "alert_id": alert.id,
                    "stock_code": alert.stock_code,
                    "error": str(e)
                })

        return triggered

    async def _build_context(self, user_id: int, stock_code: str) -> AlertContext:
        """构建策略检查上下文"""
        context = AlertContext(stock_code=stock_code, current_price=Decimal("0"))

        # 获取行情
        provider = get_quote_provider()
        quote = provider.get_quote(stock_code)
        if quote:
            context.current_price = quote.current_price or Decimal("0")
            context.open_price = quote.open_price
            context.high_price = quote.high_price
            context.low_price = quote.low_price
            context.prev_close = quote.prev_close
            context.volume = quote.volume

        # 获取持仓
        position = await self._get_position(user_id, stock_code)
        if position:
            context.position_quantity = position.quantity
            context.position_avg_cost = position.avg_cost
            if quote and quote.current_price and position.avg_cost:
                profit = (quote.current_price - position.avg_cost) * position.quantity
                profit_percent = ((quote.current_price - position.avg_cost) / position.avg_cost) * 100
                context.position_profit_loss = profit
                context.position_profit_loss_percent = profit_percent

        # 获取最近交易记录
        context.recent_transactions = await self._get_recent_transactions(user_id, stock_code, limit=5)

        # 获取历史价格（用于计算量化指标）
        history_prices = await self._get_history_prices(stock_code, limit=60)
        context.history_prices = history_prices

        # 调用量化工具计算指标
        if history_prices:
            # 提取收盘价列表（从新到旧）
            closes = []
            for item in history_prices:
                close = item.get("close") or item.get("收盘")
                if close is not None:
                    closes.append(float(close))

            if closes:
                indicators = calculate_all_indicators(closes)
                # 展开嵌套的指标数据
                flat_indicators = {}
                for key, value in indicators.items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            flat_indicators[f"{key}_{sub_key}"] = sub_value
                    else:
                        flat_indicators[key] = value
                context.indicators = flat_indicators

        return context

    async def _get_position(self, user_id: int, stock_code: str) -> Optional[Position]:
        """获取持仓"""
        result = await self.db.execute(
            select(Position).where(
                Position.user_id == user_id,
                Position.stock_code == stock_code
            )
        )
        return result.scalar_one_or_none()

    async def _get_recent_transactions(
        self,
        user_id: int,
        stock_code: str,
        limit: int = 5
    ) -> List[dict]:
        """获取最近交易记录"""
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id, Transaction.stock_code == stock_code)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        transactions = result.scalars().all()

        return [
            {
                "type": t.type,
                "quantity": t.quantity,
                "price": str(t.price),
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in transactions
        ]

    async def _get_history_prices(self, stock_code: str, limit: int = 60) -> List[dict]:
        """
        获取历史价格数据

        使用akshare获取历史K线数据
        """
        try:
            import akshare as ak

            # 判断市场
            if stock_code.startswith(('5', '6', '9')):
                market = "sh"
            else:
                market = "sz"

            symbol = f"{market}{stock_code}"

            # 获取历史数据
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                adjust=""  # 不复权
            )

            if df is None or df.empty:
                return []

            # 转换为列表（从新到旧）
            prices = []
            for _, row in df.iloc[-limit:].iterrows():
                prices.append({
                    "date": str(row.iloc[0]) if len(row) > 0 else None,
                    "open": float(row.iloc[1]) if len(row) > 1 else None,
                    "close": float(row.iloc[2]) if len(row) > 2 else None,
                    "high": float(row.iloc[3]) if len(row) > 3 else None,
                    "low": float(row.iloc[4]) if len(row) > 4 else None,
                    "volume": float(row.iloc[5]) if len(row) > 5 else None,
                    "amount": float(row.iloc[6]) if len(row) > 6 else None,
                })

            # 反转为从新到旧
            return list(reversed(prices))

        except Exception:
            return []