"""MCP/AI智能策略 - 由AI模型根据多种数据决定是否触发"""

import json
from typing import Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from decimal import Decimal

from .base import AlertStrategy, AlertContext, CheckResult


class MCPSmartStrategy(AlertStrategy):
    """
    MCP/AI智能决策策略

    此策略不使用固定规则，而是将上下文信息传递给外部AI模型，
    由AI模型综合判断是否需要触发以及建议的动作。

    config: {
        "ai_client": async_callable,  # 可选：AI客户端调用函数
        "ai_endpoint": "http://...",   # 可选：AI服务HTTP端点
        "min_confidence": 0.7,         # 最小置信度阈值
        "prompt_template": "...",      # 可选的提示词模板
    }

    ai_client 签名: async def ai_client(context: dict) -> dict
    返回格式:
    {
        "should_alert": true/false,
        "confidence": 0.0-1.0,
        "reason": "原因说明",
        "suggested_action": "BUY" / "SELL" / "NOTIFY" / "HOLD",
        "suggested_quantity": 100,  # 可选
        "suggested_price": 15.50    # 可选
    }
    """

    @property
    def strategy_type(self) -> str:
        return "MCP_SMART"

    async def check(self, context: AlertContext, config: dict) -> CheckResult:
        """
        检查是否触发提醒

        构建上下文并调用外部AI服务获取决策。
        """
        # 构建AI上下文
        ai_context = self._build_ai_context(context, config)

        # 获取AI决策
        try:
            ai_result = await self._call_ai(config, ai_context)
        except Exception as e:
            return CheckResult(
                triggered=False,
                reason=f"AI调用失败: {str(e)}",
                details={"error": str(e)}
            )

        if ai_result is None:
            return CheckResult(
                triggered=False,
                reason="AI未返回结果"
            )

        # 处理AI结果
        return self._process_ai_result(ai_result, config)

    async def _call_ai(self, config: dict, ai_context: dict) -> Optional[dict]:
        """
        调用外部AI服务

        支持两种方式：
        1. 注入的 ai_client callable
        2. HTTP endpoint
        """
        # 方式1：使用注入的 ai_client
        ai_client = config.get("ai_client")
        if ai_client and callable(ai_client):
            return await ai_client(ai_context)

        # 方式2：使用 HTTP endpoint
        ai_endpoint = config.get("ai_endpoint")
        if ai_endpoint:
            return await self._call_http_endpoint(ai_endpoint, ai_context)

        # 没有配置AI调用方式，返回模拟结果
        return self._mock_ai_response(ai_context)

    async def _call_http_endpoint(self, endpoint: str, ai_context: dict) -> Optional[dict]:
        """通过HTTP调用AI服务"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    endpoint,
                    json=ai_context,
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception:
            return None

    def _mock_ai_response(self, ai_context: dict) -> dict:
        """
        模拟AI响应（用于测试或未配置AI服务时）

        简单规则：如果RSI存在，根据RSI判断
        """
        indicators = ai_context.get("data", {}).get("量化指标", {})

        # 尝试从RSI判断
        rsi14 = None
        if "RSI14" in indicators:
            rsi_str = indicators["RSI14"].get("值", "50")
            rsi14 = float(rsi_str) if isinstance(rsi_str, str) else rsi_str

        if rsi14 is not None:
            if rsi14 >= 70:
                return {
                    "should_alert": True,
                    "confidence": 0.8,
                    "reason": f"RSI({rsi14:.1f})超买，建议卖出",
                    "suggested_action": "SELL"
                }
            elif rsi14 <= 30:
                return {
                    "should_alert": True,
                    "confidence": 0.8,
                    "reason": f"RSI({rsi14:.1f})超卖，建议买入",
                    "suggested_action": "BUY"
                }

        return {
            "should_alert": False,
            "confidence": 0.5,
            "reason": "暂无明显信号",
            "suggested_action": "HOLD"
        }

    def _process_ai_result(self, result: dict, config: dict) -> CheckResult:
        """处理AI决策结果"""
        should_alert = result.get("should_alert", False)
        confidence = result.get("confidence", 0.0)
        reason = result.get("reason", "")
        suggested_action = result.get("suggested_action", "NOTIFY")
        suggested_quantity = result.get("suggested_quantity")
        suggested_price = result.get("suggested_price")

        # 验证 suggested_action
        if suggested_action not in ("BUY", "SELL", "NOTIFY", "HOLD"):
            suggested_action = "NOTIFY"

        # 置信度检查
        min_confidence = config.get("min_confidence", 0.5)
        if should_alert and confidence < min_confidence:
            should_alert = False
            reason = f"[置信度不足:{confidence:.2f}<{min_confidence}] {reason}"

        # 转换价格
        price_decimal = None
        if suggested_price is not None:
            price_decimal = Decimal(str(suggested_price))

        return CheckResult(
            triggered=should_alert,
            reason=reason,
            suggested_action=suggested_action,
            suggested_quantity=suggested_quantity,
            suggested_price=price_decimal,
            details={
                "confidence": confidence,
                "ai_analysis": True,
                "raw_result": result
            }
        )

    def _build_ai_context(self, context: AlertContext, config: dict) -> dict:
        """构建AI决策所需的上下文"""
        prompt_template = config.get("prompt_template", self._default_prompt_template())

        # 构建上下文数据
        context_data = {
            "股票代码": context.stock_code,
            "当前价格": str(context.current_price),
            "今开": str(context.open_price) if context.open_price else None,
            "最高": str(context.high_price) if context.high_price else None,
            "最低": str(context.low_price) if context.low_price else None,
            "昨收": str(context.prev_close) if context.prev_close else None,
            "成交量": context.volume,
        }

        # 添加持仓信息
        if context.position_quantity is not None:
            context_data["持仓数量"] = context.position_quantity
            context_data["持仓成本"] = str(context.position_avg_cost) if context.position_avg_cost else None
            context_data["持仓盈亏"] = str(context.position_profit_loss) if context.position_profit_loss else None
            context_data["盈亏比例"] = f"{context.position_profit_loss_percent}%" if context.position_profit_loss_percent else None

        # 添加交易记录
        if context.recent_transactions:
            context_data["最近交易"] = context.recent_transactions[:5]

        # 添加量化指标
        if context.indicators:
            indicators = self._format_indicators(context.indicators)
            context_data["量化指标"] = indicators

        # 添加新闻
        if context.news:
            context_data["相关新闻"] = context.news[:3]

        return {
            "prompt_template": prompt_template,
            "data": context_data,
            "stock_code": context.stock_code
        }

    def _format_indicators(self, indicators: dict) -> dict:
        """格式化量化指标，使其更易读"""
        formatted = {}

        # MA指标
        for period in [5, 10, 20, 60]:
            key = f"ma{period}"
            if key in indicators:
                formatted[f"MA{period}"] = f"{indicators[key]:.2f}"

        # EMA指标
        for period in [12, 26]:
            key = f"ema{period}"
            if key in indicators:
                formatted[f"EMA{period}"] = f"{indicators[key]:.2f}"

        # MACD指标
        if "macd_macd" in indicators:
            formatted["MACD"] = {
                "DIF": f"{indicators.get('macd_macd', 0):.4f}",
                "DEA": f"{indicators.get('macd_signal', 0):.4f}",
                "柱状图": f"{indicators.get('macd_histogram', 0):.4f}",
                "趋势": indicators.get("macd_trend", "neutral")
            }

        # RSI指标
        for period in [6, 14, 24]:
            key = f"rsi{period}_rsi"
            if key in indicators:
                formatted[f"RSI{period}"] = {
                    "值": f"{indicators[key]:.2f}",
                    "区域": indicators.get(f"rsi{period}_zone", "neutral")
                }

        # 布林带
        if "bollinger_upper" in indicators:
            formatted["布林带"] = {
                "上轨": f"{indicators.get('bollinger_upper', 0):.2f}",
                "中轨": f"{indicators.get('bollinger_middle', 0):.2f}",
                "下轨": f"{indicators.get('bollinger_lower', 0):.2f}",
            }

        return formatted

    def _default_prompt_template(self) -> str:
        """默认提示词模板"""
        return """你是一个股票投资顾问。请根据以下信息做出投资决策。

## 股票信息
{data}

## 输出格式
请以JSON格式输出：
{
    "should_alert": true/false,
    "confidence": 0.0-1.0,
    "reason": "原因说明",
    "suggested_action": "BUY" 或 "SELL" 或 "NOTIFY" 或 "HOLD",
    "suggested_quantity": 建议交易数量（可选）,
    "suggested_price": 建议交易价格（可选）
}
"""