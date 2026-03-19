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
    notifier_type TEXT NOT NULL,        -- WEBSOCKET/SMTP/WEBHOOK/MCP
    notifier_config JSON,               -- 通知器配置
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

### 4.1 价格提醒策略（抽象类）

```python
from abc import ABC, abstractmethod
from typing import Any
import pandas as pd

class AlertStrategy(ABC):
    """价格提醒策略抽象基类"""

    @property
    @abstractmethod
    def strategy_type(self) -> str:
        """策略类型标识，如 'THRESHOLD', 'MA', 'MACD', 'RSI'"""
        pass

    @abstractmethod
    def check(
        self,
        current_price: float,
        history_prices: pd.DataFrame,  # 包含 open/high/low/close/volume
        config: dict[str, Any]
    ) -> bool:
        """
        检查是否触发提醒

        Args:
            current_price: 当前价格
            history_prices: 历史行情数据
            config: 策略配置参数

        Returns:
            True 表示触发提醒
        """
        pass
```

#### 策略实现示例

```python
# 阈值策略
class ThresholdAlertStrategy(AlertStrategy):
    """
    config: {"upper": 100.0, "lower": 50.0}
    价格突破上限或下限时触发
    """

# 均线策略
class MAStrategy(AlertStrategy):
    """
    config: {"period": 5, "direction": "up"}
    价格向上/向下突破均线时触发
    """

# MACD策略
class MACDStrategy(AlertStrategy):
    """
    config: {"fast": 12, "slow": 26, "signal": 9}
    MACD金叉/死叉时触发
    """

# RSI策略
class RSIStrategy(AlertStrategy):
    """
    config: {"period": 14, "overbought": 70, "oversold": 30}
    RSI进入超买/超卖区域时触发
    """
```

### 4.2 通知器（抽象类）

```python
from abc import ABC, abstractmethod
from typing import Any

class Notifier(ABC):
    """通知器抽象基类"""

    @property
    @abstractmethod
    def notifier_type(self) -> str:
        """通知器类型标识，如 'WEBSOCKET', 'SMTP', 'WEBHOOK', 'MCP'"""
        pass

    @abstractmethod
    async def send(
        self,
        user_id: int,
        title: str,
        message: str,
        config: dict[str, Any]
    ) -> bool:
        """
        发送通知

        Args:
            user_id: 目标用户ID
            title: 通知标题
            message: 通知内容
            config: 通知器配置

        Returns:
            True 表示发送成功
        """
        pass
```

#### 通知器实现示例

```python
# WebSocket通知
class WebSocketNotifier(Notifier):
    """
    config: {}  # 无需额外配置，基于用户WebSocket连接
    """

# SMTP邮件通知
class SMTPNotifier(Notifier):
    """
    config: {"to_email": "user@example.com"}
    需要全局SMTP配置
    """

# Webhook通知
class WebhookNotifier(Notifier):
    """
    config: {"url": "https://example.com/webhook", "method": "POST"}
    """

# MCP通知
class MCPNotifier(Notifier):
    """
    config: {"server_name": "my-mcp-server", "tool": "send_notification"}
    通过MCP协议调用外部工具
    """
```

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
│   │   ├── alerts.py              # (待实现)
│   │   ├── cron.py                # (待实现)
│   │   └── quote.py
│   │
│   ├── services/                  # 业务逻辑
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── position_service.py
│   │   ├── trade_service.py
│   │   ├── portfolio_service.py
│   │   └── alert_service.py       # (待实现)
│   │
│   ├── strategies/                # 价格提醒策略
│   │   ├── __init__.py
│   │   ├── base.py                # AlertStrategy抽象基类
│   │   ├── threshold.py           # 阈值策略
│   │   ├── ma.py                  # 均线策略
│   │   ├── macd.py                # MACD策略
│   │   ├── rsi.py                 # RSI策略
│   │   └── registry.py            # 策略注册表
│   │
│   ├── notifiers/                 # 通知器
│   │   ├── __init__.py
│   │   ├── base.py                # Notifier抽象基类
│   │   ├── websocket.py           # WebSocket通知
│   │   ├── smtp.py                # 邮件通知
│   │   ├── webhook.py             # Webhook通知
│   │   ├── mcp.py                 # MCP通知
│   │   └── registry.py            # 通知器注册表
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
│   └── test_alerts.py             # (待实现)
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
| **Phase 4** | 价格提醒系统（策略抽象+通知器抽象+MCP智能决策） | ✅ 已完成 |
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