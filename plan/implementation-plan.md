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

### 2.4 strategies (策略表)

```sql
CREATE TABLE strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    stock_code TEXT NOT NULL,
    strategy_name TEXT,                 -- 策略名称
    strategy_type TEXT NOT NULL,        -- THRESHOLD/MA/MACD/RSI/MCP_SMART
    strategy_config JSON NOT NULL,      -- 策略参数配置
    executor_type TEXT NOT NULL,        -- AUTO_TRADE/WEBSOCKET/WEBHOOK
    executor_config JSON,               -- 执行器配置
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
    job_type TEXT NOT NULL,             -- STRATEGY_CHECK/CUSTOM
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

### 3.5 策略管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/strategies` | 获取策略列表 |
| POST | `/api/v1/strategies` | 新增策略 |
| GET | `/api/v1/strategies/{id}` | 获取策略详情 |
| PUT | `/api/v1/strategies/{id}` | 修改策略 |
| DELETE | `/api/v1/strategies/{id}` | 删除策略 |
| GET | `/api/v1/strategies/meta/types` | 获取可用策略类型 |
| GET | `/api/v1/strategies/meta/executors` | 获取可用执行器类型 |

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

## 四、核心架构设计

### 4.1 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                           用户层                                 │
│  用户通过 API 创建策略，配置"什么条件下做什么"                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        StrategyService                          │
│  职责：策略 CRUD（创建、查询、更新、删除）                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         strategies 表                           │
│  存储：strategy_type + strategy_config + executor_type + config │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
        ┌───────────────────┐    ┌───────────────────┐
        │   手动触发检查     │    │   Cron 定时触发    │
        │   (API 调用)      │    │   (Phase 5)       │
        └───────────────────┘    └───────────────────┘
                    │                       │
                    └───────────┬───────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   StrategyContextBuilder                        │
│  职责：构建策略执行上下文                                         │
│  - 拉取行情数据（quote_provider）                                 │
│  - 拉取持仓信息（db）                                             │
│  - 拉取历史价格（akshare）                                        │
│  - 拉取交易记录（db）                                             │
│  - 不计算量化指标，由策略器按需调用 quant 模块                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       StrategyContext                           │
│  数据：user_id, stock_code, 行情, 持仓, 历史价格, 交易记录        │
│  不含量化指标，由策略器内部调用 quant 模块计算                     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BaseStrategy.check()                       │
│  职责：根据 context 和 config 判断是否触发                         │
│  返回：CheckResult(triggered, reason, suggested_action, ...)    │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
            triggered=True           triggered=False
                    │                       │
                    ▼                       └── 结束
┌─────────────────────────────────────────────────────────────────┐
│                         Executor.execute()                      │
│  职责：执行触发后的动作                                           │
│  - AutoTradeExecutor → TradeService                             │
│  - WebSocketExecutor → 推送通知                                  │
│  - WebhookExecutor → HTTP 回调                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 量化工具模块（独立模块）

量化计算逻辑独立于策略，便于复用和测试。

```
app/quant/
├── __init__.py      # 统一导出
├── ma.py            # MA 计算
├── ema.py           # EMA 计算
├── macd.py          # MACD 计算（依赖 ema）
├── rsi.py           # RSI 计算
├── bollinger.py     # 布林带计算
└── indicators.py    # calculate_all_indicators 综合计算
```

**设计原则**：
- 所有函数接收价格列表（从新到旧排序）
- 返回值均为基本类型（float/dict），便于序列化
- 计算逻辑独立，不依赖外部状态

**调用方**：
- `StrategyContextBuilder.calculate_indicators()` 构建上下文时调用
- 策略类可按需调用（如历史数据不足时补充计算）

---

### 4.3 StrategyContext（策略上下文）

```python
@dataclass
class StrategyContext:
    """策略执行上下文（原始数据，不包含量化指标）"""
    # 基础信息
    user_id: int
    stock_code: str

    # 行情数据
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
    position_profit_loss_percent: Optional[Decimal] = None

    # 交易记录
    recent_transactions: list[dict] = field(default_factory=list)

    # 历史价格（用于量化计算）
    history_prices: list[dict] = field(default_factory=list)
```

**设计原则**：
- 只存储原始数据，不预计算量化指标
- 量化指标由策略器内部按需调用 `quant` 模块计算
- 量化计算是纯 CPU 操作，没有 IO 开销，性能影响可忽略

---

### 4.4 StrategyContextBuilder（上下文构建器）

```python
class StrategyContextBuilder:
    """策略上下文构建器"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def build(self, user_id: int, stock_code: str) -> StrategyContext:
        """构建策略上下文"""
        pass

    # 私有方法
    async def _fetch_quote(self, context: StrategyContext) -> None: pass
    async def _fetch_position(self, context: StrategyContext) -> None: pass
    async def _fetch_recent_transactions(self, context: StrategyContext) -> None: pass
    async def _fetch_history_prices(self, context: StrategyContext) -> None: pass
```

**设计原则**：
- 只负责拉取数据（行情、持仓、历史价格、交易记录）
- 不计算量化指标，由策略器按需调用 `quant` 模块

---

### 4.5 BaseStrategy（策略基类）

```python
@dataclass
class CheckResult:
    """策略检查结果"""
    triggered: bool
    reason: Optional[str] = None
    suggested_action: str = "NOTIFY"  # BUY/SELL/NOTIFY/HOLD
    suggested_quantity: Optional[int] = None
    suggested_price: Optional[Decimal] = None
    details: dict[str, Any] = field(default_factory=dict)


class BaseStrategy(ABC):
    """策略抽象基类"""

    @property
    @abstractmethod
    def strategy_type(self) -> str:
        """策略类型标识"""
        pass

    @abstractmethod
    async def check(
        self,
        context: StrategyContext,
        config: dict[str, Any]
    ) -> CheckResult:
        """
        检查是否触发

        Args:
            context: 策略执行上下文（行情、持仓、历史价格、量化指标）
            config: 策略配置参数

        Returns:
            CheckResult 包含是否触发、原因、建议动作等
        """
        pass
```

#### 策略实现示例

```python
# 阈值策略 - 不依赖量化指标
class ThresholdStrategy(BaseStrategy):
    """
    config: {"upper": 100.0, "lower": 50.0, "action_on_upper": "SELL"}
    价格突破上限或下限时触发
    """

# 均线策略 - 调用quant模块计算MA
class MAStrategy(BaseStrategy):
    """
    config: {"period": 5, "direction": "up", "action_on_up": "BUY"}

    内部调用 quant.calculate_ma(context.history_prices, period)
    """

# MACD策略 - 调用quant模块计算MACD
class MACDStrategy(BaseStrategy):
    """
    config: {"type": "golden_cross", "action_on_golden": "BUY"}

    内部调用 quant.calculate_macd(context.history_prices)
    """

# RSI策略 - 调用quant模块计算RSI
class RSIStrategy(BaseStrategy):
    """
    config: {"period": 14, "overbought": 70, "action_on_overbought": "SELL"}

    内部调用 quant.calculate_rsi(context.history_prices, period)
    """

# MCP智能策略 - 调用quant模块计算所有指标，交给AI判断
class MCPSmartStrategy(BaseStrategy):
    """
    config: {"ai_client": callable, "min_confidence": 0.7}

    工作流程：
    1. 从context获取原始数据
    2. 调用 quant.calculate_all_indicators() 计算量化指标
    3. 构建AI上下文，调用外部AI服务
    4. 返回CheckResult
    """
```

---

### 4.6 Executor（执行器）

执行器负责策略触发后的动作。

```python
@dataclass
class ExecutionRequest:
    """执行请求"""
    user_id: int
    stock_code: str
    action: str  # BUY/SELL/NOTIFY
    quantity: Optional[int] = None
    price: Optional[Decimal] = None
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    action: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


class Executor(ABC):
    """执行器抽象基类"""

    @property
    @abstractmethod
    def executor_type(self) -> str:
        """执行器类型标识"""
        pass

    @abstractmethod
    async def execute(
        self,
        request: ExecutionRequest,
        config: dict[str, Any]
    ) -> ExecutionResult:
        """执行动作"""
        pass
```

#### 执行器实现示例

```python
# 自动交易执行器
class AutoTradeExecutor(Executor):
    """
    executor_type: "AUTO_TRADE"
    收到触发后调用 TradeService 完成买入/卖出
    """

# WebSocket通知执行器
class WebSocketExecutor(Executor):
    """
    executor_type: "WEBSOCKET"
    通过WebSocket推送消息给用户
    """

# Webhook执行器
class WebhookExecutor(Executor):
    """
    executor_type: "WEBHOOK"
    调用外部HTTP接口
    """
```

#### 策略器与执行器的组合

| 策略器 | 执行器 | 场景 |
|--------|--------|------|
| ThresholdStrategy | AutoTradeExecutor | 阈值自动交易 |
| MAStrategy | WebSocketExecutor | 均线信号提醒 |
| MCPSmartStrategy | AutoTradeExecutor | AI自动模拟交易 |
| MCPSmartStrategy | WebSocketExecutor | AI建议人工执行 |

---

### 4.7 StrategyExecutor（策略执行器 - Phase 5）

```python
class StrategyExecutor:
    """策略执行器（Cron 调用）"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.context_builder = StrategyContextBuilder(db)

    async def check_and_execute(self, strategy_id: int) -> ExecutionResult:
        """检查单个策略并执行"""
        # 1. 获取策略
        # 2. 构建上下文
        # 3. 调用策略检查
        # 4. 如果触发，调用执行器
        pass

    async def check_all(self, user_id: int = None) -> list[dict]:
        """检查所有启用的策略"""
        pass
```

---

## 五、模块职责划分

| 模块 | 文件 | 职责 |
|------|------|------|
| **StrategyService** | `app/services/strategy_service.py` | 策略 CRUD |
| **StrategyContext** | `app/strategies/context.py` | 策略执行上下文数据结构 |
| **StrategyContextBuilder** | `app/strategies/context_builder.py` | 构建上下文（拉取数据、计算指标） |
| **BaseStrategy** | `app/strategies/base.py` | 策略抽象基类 |
| **StrategyExecutor** | `app/scheduler/strategy_executor.py` | 定时执行策略检查（Phase 5） |
| **TradeService** | `app/services/trade_service.py` | 交易执行（买入、卖出） |
| **quant** | `app/quant/` | 量化指标计算 |

---

## 六、项目目录结构

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
│   │   ├── strategy.py            # Strategy 模型
│   │   └── cron_job.py
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── position.py
│   │   ├── transaction.py
│   │   ├── strategy.py            # StrategyCreate/Update/Response
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
│   │   ├── strategies.py          # 策略 API
│   │   ├── cron.py                # (Phase 5)
│   │   └── quote.py
│   │
│   ├── services/                  # 业务逻辑
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── position_service.py
│   │   ├── trade_service.py
│   │   ├── portfolio_service.py
│   │   └── strategy_service.py    # 策略 CRUD
│   │
│   ├── quant/                     # 量化指标计算
│   │   ├── __init__.py
│   │   ├── ma.py
│   │   ├── ema.py
│   │   ├── macd.py
│   │   ├── rsi.py
│   │   ├── bollinger.py
│   │   └── indicators.py
│   │
│   ├── strategies/                # 策略模块
│   │   ├── __init__.py
│   │   ├── base.py                # BaseStrategy + StrategyContext + CheckResult
│   │   ├── context_builder.py     # StrategyContextBuilder
│   │   ├── registry.py            # 策略注册表
│   │   ├── threshold.py           # 阈值策略
│   │   ├── ma.py                  # 均线策略
│   │   ├── macd.py                # MACD策略
│   │   ├── rsi.py                 # RSI策略
│   │   └── mcp.py                 # MCP智能策略
│   │
│   ├── executors/                 # 执行器
│   │   ├── __init__.py
│   │   ├── base.py                # Executor + ExecutionRequest + ExecutionResult
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
│   ├── scheduler/                 # 定时任务（Phase 5）
│   │   ├── __init__.py
│   │   ├── manager.py             # APScheduler管理
│   │   ├── strategy_executor.py   # StrategyExecutor
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
│   ├── test_strategies_api.py     # 策略 API 测试
│   ├── test_strategy_impl.py      # 策略实现测试
│   ├── test_executors.py          # 执行器测试
│   └── test_quant.py              # 量化模块测试
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

## 七、实现阶段

| 阶段 | 任务 | 状态 |
|------|------|------|
| **Phase 1** | 项目初始化、配置、数据库模型 | ✅ 已完成 |
| **Phase 2** | 用户API、持仓管理API | ✅ 已完成 |
| **Phase 3** | 交易API、资产估值API（雪球行情） | ✅ 已完成 |
| **Phase 4** | 策略系统（策略抽象+执行器抽象+量化模块） | ✅ 已完成 |
| **Phase 4.5** | 架构重构：命名统一、职责分离、ContextBuilder | 🔄 进行中 |
| **Phase 5** | 定时任务系统（APScheduler + StrategyExecutor） | 📋 待开发 |
| **Phase 6** | WebSocket实时推送 | 📋 待开发 |

---

## 八、依赖包

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
httpx>=0.26.0                      # 异步HTTP客户端
```