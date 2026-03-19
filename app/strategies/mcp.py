"""MCP/AI智能策略 - 由AI模型根据多种数据决定是否触发通知"""

import json
from typing import Any

from .base import AlertStrategy, AlertContext, CheckResult


class MCPSmartStrategy(AlertStrategy):
    """
    MCP/AI智能决策策略

    此策略不使用固定规则，而是将上下文信息传递给外部AI模型（通过MCP工具调用），
    由AI模型根据：
    - 用户持仓情况
    - 交易记录
    - 当前行情
    - 量化指标结果（MA/MACD/RSI/布林带等，由quant模块计算）
    - 相关新闻
    等多维度数据综合判断是否需要发送通知。

    量化指标说明：
    - AlertService在构建上下文时会自动调用量化工具计算指标
    - 指标结果存储在context.indicators中，包含：
      - ma5, ma10, ma20, ma60: 移动平均线
      - ema12, ema26: 指数移动平均线
      - macd_macd, macd_signal, macd_histogram, macd_trend: MACD指标
      - rsi6_rsi, rsi6_zone, rsi14_rsi, rsi14_zone: RSI指标
      - bollinger_upper, bollinger_middle, bollinger_lower: 布林带

    config: {
        "mcp_server": "my-mcp-server",  # MCP服务器名称
        "tool": "analyze_alert",         # MCP工具名称
        "prompt_template": "...",        # 可选的提示词模板
        "min_confidence": 0.7,           # 最小置信度阈值
        "cooldown_minutes": 30           # 冷却时间（分钟）
    }
    """

    @property
    def strategy_type(self) -> str:
        return "MCP_SMART"

    def check(self, context: AlertContext, config: dict) -> CheckResult:
        """
        检查是否触发提醒

        注意：此策略的实际AI决策逻辑需要在运行时通过MCP调用外部AI服务。
        这里提供的是框架和接口定义，具体的MCP调用由AlertService处理。
        """
        # 构建传递给AI的上下文
        ai_context = self._build_ai_context(context, config)

        # 返回需要AI决策的标记
        # AlertService会检测到这个结果并调用MCP工具
        return CheckResult(
            triggered=False,  # 初始不触发，等待AI决策
            reason="PENDING_AI_DECISION",
            details={
                "requires_ai_decision": True,
                "ai_context": ai_context,
                "config": config
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
            context_data["最近交易"] = context.recent_transactions[:5]  # 最近5笔

        # 添加量化指标（由quant模块计算）
        if context.indicators:
            # 格式化量化指标数据
            indicators = self._format_indicators(context.indicators)
            context_data["量化指标"] = indicators

        # 添加新闻
        if context.news:
            context_data["相关新闻"] = context.news[:3]  # 最近3条

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
                "带宽": f"{indicators.get('bollinger_bandwidth', 0):.2f}%",
                "价格位置": f"{indicators.get('bollinger_position', 50):.1f}%"
            }

        return formatted

    def _default_prompt_template(self) -> str:
        """默认提示词模板"""
        return """你是一个股票投资顾问。请根据以下信息判断是否需要向用户发送提醒通知。

## 股票信息
{data}

## 量化指标说明
- MA5/MA10/MA20/MA60: 移动平均线，价格在MA上方为多头，下方为空头
- MACD: DIF上穿DEA为金叉(看涨)，下穿为死叉(看跌)
- RSI: >70超买(风险)，<30超卖(机会)
- 布林带: 价格触及上轨可能回调，触及下轨可能反弹

## 判断标准
请综合考虑以下因素：
1. 价格异动：是否出现显著的价格变化
2. 技术指标：MA/MACD/RSI/布林带等指标是否发出信号
3. 持仓情况：用户当前盈亏状态，是否需要止盈止损提醒
4. 交易记录：近期的交易行为是否有异常
5. 新闻动态：相关新闻是否可能影响股价

## 输出格式
请以JSON格式输出你的判断：
{
    "should_alert": true/false,
    "confidence": 0.0-1.0,
    "reason": "触发原因说明",
    "suggested_action": "建议操作（如：建议关注、考虑止盈等）"
}
"""


class AIAnalysisResult:
    """AI分析结果"""

    def __init__(self, raw_response: dict):
        self.should_alert = raw_response.get("should_alert", False)
        self.confidence = raw_response.get("confidence", 0.0)
        self.reason = raw_response.get("reason", "")
        self.suggested_action = raw_response.get("suggested_action", "")
        self.raw_response = raw_response

    def to_check_result(self) -> CheckResult:
        """转换为CheckResult"""
        return CheckResult(
            triggered=self.should_alert,
            reason=self.reason,
            details={
                "confidence": self.confidence,
                "suggested_action": self.suggested_action,
                "ai_analysis": True
            }
        )