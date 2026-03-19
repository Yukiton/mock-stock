# 模拟炒股后端API项目 - 实现计划

## 一、技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| **Web框架** | FastAPI | 高性能异步、自动OpenAPI文档、类型提示友好 |
| **ORM** | SQLAlchemy 2.0 | 成熟稳定、支持异步、类型安全 |
| **数据库** | SQLite | 轻量级、零配置、符合需求 |
| **定时任务** | APScheduler | 支持cron、持久化、与FastAPI集成良好 |
| **行情数据** | akshare `stock_individual_spot_xq()` | 雪球实时行情，支持股票和ETF，无需缓存 |
| **依赖注入** | FastAPI Depends | 解耦组件 |
| **配置管理** | pydantic-settings | 类型安全的配置 |
| **WebSocket** | FastAPI原生 | 实时价格推送 |

---

## 二、数据库表设计

### 2.1 users (用户表)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    balance DECIMAL(15,2) DEFAULT 0.00,  -- 可用现金余额
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 positions (持仓表)

```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    stock_code TEXT NOT NULL,           -- 股票代码如 "000001"
    stock_name TEXT,                    -- 股票名称
    quantity INTEGER DEFAULT 0,         -- 持仓数量（股）
    avg_cost DECIMAL(10,4) DEFAULT 0,   -- 持仓成本价
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, stock_code)         -- 每用户每股票唯一
);
```

### 2.3 transactions (交易记录表)

```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    stock_code TEXT NOT NULL,
    stock_name TEXT,
    type TEXT NOT NULL,                 -- "BUY" / "SELL"
    quantity INTEGER NOT NULL,
    price DECIMAL(10,4) NOT NULL,       -- 成交价格（可自定义）
    amount DECIMAL(15,2) NOT NULL,      -- 成交金额
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 2.4 price_alerts (价格提醒表)

```sql
CREATE TABLE price_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    stock_code TEXT NOT NULL,
    alert_name TEXT,                    -- 提醒名称
    strategy_type TEXT NOT NULL,        -- THRESHOLD/MA/MACD/RSI/CUSTOM
    strategy_config JSON NOT NULL,      -- 策略参数配置
    notifier_type TEXT NOT NULL,        -- AUTO_TRADE/WEBSOCKET/WEBHOOK
    notifier_config JSON,               -- 执行器配置
    enabled BOOLEAN DEFAULT TRUE,
    last_triggered_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 2.5 cron_jobs (定时任务配置表)

```sql
-- 注意：cron_jobs为全局任务，不关联user_id
CREATE TABLE cron_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    cron_expression TEXT NOT NULL,      -- cron表达式
    job_type TEXT NOT NULL,             -- PRICE_CHECK/ALERT_CHECK/CUSTOM
    config JSON,                        -- 任务配置
    enabled BOOLEAN DEFAULT TRUE,
    last_run_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 三、API接口设计

### 3.1 用户与资产

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/users/register` | 用户注册 |
| POST | `/api/v1/users/login` | 用户登录 |
| GET | `/api/v1/users/me` | 获取当前用户信息 |
| GET | `/api/v1/users/me/balance` | 获取账户余额 |
| PUT | `/api/v1/users/me/balance` | 手动调整余额 |

### 3.2 持仓管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/positions` | 获取持仓列表 |
| POST | `/api/v1/positions` | 新增持仓记录 |
| GET | `/api/v1/positions/{stock_code}` | 获取单只股票持仓详情 |
| PUT | `/api/v1/positions/{stock_code}` | 手动调整持仓 |
| DELETE | `/api/v1/positions/{stock_code}` | 清空持仓 |

### 3.3 资产估值

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/portfolio/value` | 股票持仓总市值 |
| GET | `/api/v1/portfolio/total` | 总资产 = 现金 + 股票市值 |
| GET | `/api/v1/portfolio/profit-loss` | 持仓参考盈亏 |

### 3.4 交易操作

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/trade/buy` | 买入（可自定义价格） |
| POST | `/api/v1/trade/sell` | 卖出（可自定义价格） |
| GET | `/api/v1/trade/history` | 交易历史记录 |

### 3.5 价格提醒

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/alerts` | 获取提醒列表 |
| POST | `/api/v1/alerts` | 新增价格提醒 |
| PUT | `/api/v1/alerts/{id}` | 修改价格提醒 |
| DELETE | `/api/v1/alerts/{id}` | 删除价格提醒 |

### 3.6 定时任务

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/cron-jobs` | 获取定时任务列表 |
| POST | `/api/v1/cron-jobs` | 新增定时任务 |
| PUT | `/api/v1/cron-jobs/{id}` | 修改定时任务 |
| DELETE | `/api/v1/cron-jobs/{id}` | 删除定时任务 |

### 3.7 实时行情

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/quote/{stock_code}` | 获取单只股票实时行情 |
| GET | `/api/v1/quote/batch` | 批量获取行情 |
| WS | `/ws/quote/{stock_code}` | WebSocket实时行情推送 |

---

## 四、核心抽象设计

### 4.1 量化工具模块（独立模块）

量化计算逻辑独立于策略，便于复用和测试。

```python
# app/quant/indicators.py

def calculate_ma(prices: list[float], period: int) -> float | None:
    """计算简单移动平均线"""
    pass

def calculate_ema(prices: list[float], period: int) -> float | None:
    """计算指数移动平均线"""
    pass

def calculate_macd(prices: list[float], fast=12, slow=26, signal=9) -> dict | None:
    """计算MACD指标"""
    pass

def calculate_rsi(prices: list[float], period=14) -> dict | None:
    """计算RSI指标"""
    pass

def calculate_bollinger(prices: list[float], period=20, std_dev=2.0) -> dict | None:
    """计算布林带"""
    pass

def calculate_all_indicators(prices: list[float]) -> dict:
    """一次性计算所有指标，返回统一结果"""
    pass
```

**设计原则**：
- 所有函数接收价格列表（从新到旧排序）
- 返回值均为基本类型（float/dict），便于序列化
- 计算逻辑独立，不依赖外部状态

**调用方**：
1. `AlertService._build_context()` 构建上下文时调用，结果存入 `context.indicators`
2. 策略类可按需调用（如历史数据不足时补充计算）
3. MCP 智能策略通过 `context.indicators` 获取结果

---

### 4.2 价格提醒策略（抽象类）

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional

@dataclass
class AlertContext:
    """策略检查上下文"""
    stock_code: str
    current_price: Decimal
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    prev_close: Optional[Decimal] = None
    volume: Optional[int] = None
    # 持仓信息
    position_quantity: Optional[int] = None
    position_avg_cost: Optional[Decimal] = None
    position_profit_loss: Optional[Decimal] = None
    position_profit_loss_percent: Optional[float] = None
    # 历史数据
    history_prices: list[dict[str, Any]] = field(default_factory=list)
    recent_transactions: list[dict[str, Any]] = field(default_factory=list)
    # 量化指标（由AlertService调用quant模块计算）
    indicators: dict[str, Any] = field(default_factory=dict)
    # 新闻
    news: list[dict[str, Any]] = field(default_factory=list)


class AlertStrategy(ABC):
    """价格提醒策略抽象基类"""

    @property
    @abstractmethod
    def strategy_type(self) -> str:
        """策略类型标识"""
        pass

    @abstractmethod
    def check(self, context: AlertContext, config: dict) -> CheckResult:
        """
        检查是否触发提醒

        Args:
            context: 包含行情、持仓、量化指标等的上下文
            config: 策略配置参数

        Returns:
            CheckResult 包含是否触发、原因、详情
        """
        pass
```

#### 策略实现示例

```python
# 阈值策略 - 不依赖量化指标
class ThresholdStrategy(AlertStrategy):
    """
    config: {"upper": 100.0, "lower": 50.0, "percent_upper": 5.0}
    价格突破上限或下限时触发
    """

# 均线策略 - 从context.indicators获取MA值
class MAStrategy(AlertStrategy):
    """
    config: {"period": 5, "direction": "up"}
    从context.indicators["ma5"]获取均线值
    """

# MACD策略 - 从context.indicators获取MACD值
class MACDStrategy(AlertStrategy):
    """
    config: {"trigger": "golden_cross"}  # golden_cross / death_cross
    从context.indicators["macd_*"]获取指标
    """

# RSI策略 - 从context.indicators获取RSI值
class RSIStrategy(AlertStrategy):
    """
    config: {"period": 14, "overbought": 70, "oversold": 30}
    从context.indicators["rsi14_*"]获取指标
    """

# MCP智能策略 - 综合判断
class MCPSmartStrategy(AlertStrategy):
    """
    config: {"mcp_server": "...", "tool": "...", "min_confidence": 0.7}

    工作流程：
    1. AlertService._build_context() 调用 quant.calculate_all_indicators()
    2. 指标结果存入 context.indicators（扁平化格式）:
       - ma5, ma10, ma20, ma60
       - ema12, ema26
       - macd_macd, macd_signal, macd_histogram, macd_trend
       - rsi6_rsi, rsi6_zone, rsi14_rsi, rsi14_zone
       - bollinger_upper, bollinger_middle, bollinger_lower
    3. MCPSmartStrategy._format_indicators() 格式化指标为易读格式
    4. 构建AI上下文，包含：股票信息、持仓、交易记录、量化指标、新闻
    5. 返回 requires_ai_decision=True，由外部MCP服务决策
    """
```

**量化指标流向**：

```
akshare历史数据
       ↓
AlertService._get_history_prices()
       ↓
quant.calculate_all_indicators(closes)
       ↓
context.indicators (扁平化字典)
       ↓
┌──────────────────┬─────────────────────┐
│                  │                     │
MAStrategy         RSIStrategy         MCPSmartStrategy
(直接使用)         (直接使用)          (_format_indicators格式化后交给AI)
```

### 4.3 执行器（抽象类）

执行器负责策略触发后的动作，策略器只返回 true/false + 建议操作，执行器负责具体执行。

```python
from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass

@dataclass
class ExecutionRequest:
    """执行请求"""
    user_id: int
    stock_code: str
    action: str  # "BUY" / "SELL" / "NOTIFY"
    quantity: int | None = None
    price: float | None = None
    reason: str = ""
    details: dict[str, Any] = None

class Executor(ABC):
    """执行器抽象基类"""

    @property
    @abstractmethod
    def executor_type(self) -> str:
        """执行器类型标识"""
        pass

    @abstractmethod
    async def execute(self, request: ExecutionRequest) -> bool:
        """
        执行动作

        Args:
            request: 执行请求

        Returns:
            True 表示执行成功
        """
        pass
```

#### 执行器实现示例

```python
# 自动交易执行器
class AutoTradeExecutor(Executor):
    """
    executor_type: "AUTO_TRADE"

    收到触发后自动调用交易API完成买入/卖出。
    适用于：AI自动模拟交易、传统量化自动交易。
    """

    async def execute(self, request: ExecutionRequest) -> bool:
        if request.action == "BUY":
            # 调用 TradeService.buy()
            pass
        elif request.action == "SELL":
            # 调用 TradeService.sell()
            pass
        return True

# WebSocket通知执行器
class WebSocketExecutor(Executor):
    """
    executor_type: "WEBSOCKET"

    通过WebSocket推送消息给用户。
    适用于：AI建议人工执行、传统量化信号提醒。
    """

    async def execute(self, request: ExecutionRequest) -> bool:
        # 推送消息到用户
        pass

# Webhook执行器
class WebhookExecutor(Executor):
    """
    executor_type: "WEBHOOK"

    调用外部HTTP接口。
    适用于：对接第三方通知服务。
    """

    async def execute(self, request: ExecutionRequest) -> bool:
        # 发送HTTP请求
        pass
```

#### 策略器与执行器的组合

| 策略器 | 执行器 | 场景 |
|--------|--------|------|
| MAStrategy | AutoTradeExecutor | 均线突破自动交易 |
| RSIStrategy | WebSocketExecutor | RSI信号提醒 |
| MCPSmartStrategy | AutoTradeExecutor | AI自动模拟交易 |
| MCPSmartStrategy | WebSocketExecutor | AI建议人工执行 |

---

## 五、项目目录结构

```
mock-stock/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI入口
│   ├── config.py                  # 配置管理
│   ├── auth.py                    # JWT认证
│   │
│   ├── models/                    # SQLAlchemy模型
│   │   ├── __init__.py
│   │   ├── base.py                # 基础模型类
│   │   ├── user.py
│   │   ├── position.py
│   │   ├── transaction.py
│   │   ├── price_alert.py
│   │   └── cron_job.py
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── position.py
│   │   ├── transaction.py
│   │   ├── alert.py
│   │   ├── portfolio.py
│   │   └── common.py
│   │
│   ├── api/                       # API路由
│   │   ├── __init__.py
│   │   ├── router.py              # 总路由
│   │   ├── users.py
│   │   ├── positions.py
│   │   ├── portfolio.py
│   │   ├── trade.py
│   │   ├── alerts.py              # ✅ 已实现
│   │   ├── cron.py                # (待实现)
│   │   └── quote.py
│   │
│   ├── services/                  # 业务逻辑
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── position_service.py
│   │   ├── trade_service.py
│   │   ├── portfolio_service.py
│   │   └── alert_service.py       # ✅ 已实现（调用quant模块）
│   │
│   ├── quant/                     # 量化指标计算（独立模块）
│   │   ├── __init__.py
│   │   └── indicators.py          # MA/EMA/MACD/RSI/Bollinger
│   │
│   ├── strategies/                # 价格提醒策略
│   │   ├── __init__.py
│   │   ├── base.py                # AlertStrategy + AlertContext
│   │   ├── threshold.py           # 阈值策略
│   │   ├── ma.py                  # 均线策略（使用quant模块）
│   │   ├── macd.py                # MACD策略（使用quant模块）
│   │   ├── rsi.py                 # RSI策略（使用quant模块）
│   │   ├── mcp.py                 # MCP智能策略（AI综合决策）
│   │   └── registry.py            # 策略注册表
│   │
│   ├── executors/                 # 执行器
│   │   ├── __init__.py
│   │   ├── base.py                # Executor抽象基类
│   │   ├── auto_trade.py          # 自动交易执行器
│   │   ├── websocket.py           # WebSocket通知执行器
│   │   ├── webhook.py             # Webhook执行器
│   │   └── registry.py            # 执行器注册表
│   │
│   ├── quote/                     # 行情数据
│   │   ├── __init__.py
│   │   ├── base.py                # 行情提供者接口
│   │   └── akshare_provider.py    # akshare实现(雪球接口)
│   │
│   ├── scheduler/                 # 定时任务
│   │   ├── __init__.py
│   │   ├── manager.py             # APScheduler管理
│   │   └── jobs.py                # 任务定义
│   │
│   └── db/                        # 数据库
│       ├── __init__.py
│       ├── database.py            # 数据库连接
│       └── init_db.py             # 初始化脚本
│
├── tests/                         # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_models.py
│   ├── test_users.py
│   ├── test_positions.py
│   ├── test_trade.py
│   ├── test_portfolio.py
│   ├── test_alerts.py             # ✅ 已实现
│   └── test_quant.py              # ✅ 已实现
│
├── plan/                          # 文档
│   ├── requirements.md
│   ├── implementation-plan.md
│   ├── akfamily_tutorial.md
│   ├── fund_public.md
│   └── stock.md
│
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 六、实现阶段

| 阶段 | 任务 | 状态 |
|------|------|------|
| **Phase 1** | 项目初始化、配置、数据库模型 | ✅ 已完成 |
| **Phase 2** | 用户API、持仓管理API | ✅ 已完成 |
| **Phase 3** | 交易API、资产估值API（雪球行情） | ✅ 已完成 |
| **Phase 4** | 价格提醒系统（策略抽象+执行器抽象+AI智能决策） | ✅ 已完成 |
| **Phase 5** | 定时任务系统（APScheduler集成） | 📋 待开发 |
| **Phase 6** | WebSocket实时推送 | 📋 待开发 |

---

## 七、依赖包

```
# requirements.txt
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.0
aiosqlite>=0.19.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
apscheduler>=3.10.0
python-jose[cryptography]>=3.3.0  # JWT
passlib[bcrypt]>=1.7.4             # 密码哈希
akshare>=1.12.0
pandas>=2.0.0
requests>=2.31.0
aiosmtplib>=3.0.0                  # 异步SMTP
httpx>=0.26.0                      # 异步HTTP客户端
```