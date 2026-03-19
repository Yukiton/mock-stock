# Mock Stock Trading Backend

> **⚠️ 免责声明：本项目由 AI（Claude）辅助实现，仅供学习和研究目的，不构成任何投资建议。**

一个基于 FastAPI 的模拟炒股后端系统，用于测试 AI 辅助投资决策的效果。

## 项目目的

本项目旨在构建一个 **AI 辅助投资决策闭环**：

```
数据采集 → 量化分析 → AI 决策 → 执行交易 → 跟踪收益
```

核心问题是：**AI 给出的投资建议，能不能赚钱？**

## 设计理念

### 为什么"只发提醒不自动交易"？

这并非功能缺失，而是有意为之的设计：

- **决策逻辑外置**：后端只负责数据采集、量化计算、交易执行，"大脑"在外部 AI 模型
- **灵活切换**：可以接入不同的 AI 模型进行对比测试

### 两种使用模式

**模式一：AI 自动模拟交易**

```
行情数据 + 持仓信息 + 量化指标
         ↓
    外部 AI 模型决策
         ↓
   AI 直接调用交易 API
         ↓
    模拟账户完成交易
         ↓
    更新后的持仓供下次决策
```

AI 模型通过 MCP 协议直接调用 `/trade/buy`、`/trade/sell` API，完成自动化的模拟交易闭环。

**模式二：AI 建议 + 人工执行 + 数据回传**

```
行情数据 + 持仓信息 + 量化指标
         ↓
    外部 AI 模型决策
         ↓
    推送建议给用户
         ↓
   用户在真实市场执行交易
         ↓
   用户调用 API 记录交易结果
         ↓
    更新后的持仓供下次 AI 决策
```

用户收到 AI 建议后，在真实市场交易，然后调用 API 更新持仓数据。这样 AI 可以持续跟踪真实的持仓变化，为下一轮决策提供准确依据。

两种模式的核心都是：**AI 持续跟踪持仓变化，做出下一轮决策**。

### 为什么交易价格可自定义？

在"模式二"中，用户在真实市场交易后，需要记录实际成交价格：

- AI 建议买入时价格为 P₁
- 用户实际成交价格为 P₂（可能有滑点、延迟）
- 用户按 P₂ 调用 API 记录交易，确保持仓成本准确

这样 AI 下次决策时，基于的是真实的持仓成本，而非理论价格。

## 功能特性

### 用户系统
- 用户注册与登录（JWT 认证）
- 账户余额管理

### 交易系统
- 股票买入/卖出
- 持仓成本均价计算
- 交易历史记录查询

### 行情系统
- 实时股票行情（基于 akshare）
- 批量行情查询
- 持仓市值与盈亏计算

### 价格提醒系统
- **策略模式**：支持多种提醒策略
  - `THRESHOLD`：阈值策略（价格上限/下限、涨跌幅）
  - `MA`：均线策略（MA5/MA10/MA20/MA60 突破）
  - `MACD`：MACD 策略（金叉/死叉）
  - `RSI`：RSI 策略（超买/超卖）
  - `MCP_SMART`：AI 智能策略（由外部 AI 模型决策）

- **通知器模式**：支持多种通知方式
  - `WEBSOCKET`：WebSocket 实时推送
  - `WEBHOOK`：HTTP Webhook 回调
  - `MCP`：MCP 服务通知

### 量化指标计算
独立量化工具模块，支持：
- MA（简单移动平均线）
- EMA（指数移动平均线）
- MACD（异同移动平均线）
- RSI（相对强弱指数）
- Bollinger Bands（布林带）

## 技术栈

- **框架**：FastAPI + Uvicorn
- **数据库**：SQLite（异步 SQLAlchemy）
- **认证**：JWT（python-jose）+ bcrypt
- **行情数据**：akshare
- **任务调度**：APScheduler
- **测试**：pytest + pytest-asyncio

## 项目结构

```
mock-stock/
├── app/
│   ├── api/              # API 路由
│   │   ├── users.py      # 用户接口
│   │   ├── trade.py      # 交易接口
│   │   ├── positions.py  # 持仓接口
│   │   ├── portfolio.py  # 投资组合接口
│   │   ├── quote.py      # 行情接口
│   │   └── alerts.py     # 价格提醒接口
│   ├── models/           # 数据模型
│   │   ├── user.py
│   │   ├── position.py
│   │   ├── transaction.py
│   │   └── price_alert.py
│   ├── schemas/          # Pydantic 模式
│   ├── services/         # 业务逻辑
│   │   ├── user_service.py
│   │   ├── trade_service.py
│   │   ├── position_service.py
│   │   ├── portfolio_service.py
│   │   └── alert_service.py
│   ├── strategies/       # 价格提醒策略
│   │   ├── base.py       # 策略基类
│   │   ├── threshold.py  # 阈值策略
│   │   ├── ma.py         # 均线策略
│   │   ├── macd.py       # MACD 策略
│   │   ├── rsi.py        # RSI 策略
│   │   └── mcp.py        # AI 智能策略
│   ├── notifiers/        # 通知器
│   │   ├── base.py       # 通知器基类
│   │   ├── websocket.py  # WebSocket 通知
│   │   ├── webhook.py    # Webhook 通知
│   │   └── mcp.py        # MCP 通知
│   ├── quant/            # 量化指标计算
│   │   └── indicators.py
│   ├── quote/            # 行情数据源
│   │   └── akshare_provider.py
│   ├── db/               # 数据库配置
│   ├── auth.py           # 认证模块
│   ├── config.py         # 配置管理
│   └── main.py           # 应用入口
├── tests/                # 测试文件
│   ├── test_users.py
│   ├── test_trade.py
│   ├── test_portfolio.py
│   ├── test_alerts.py
│   └── test_quant.py
├── requirements.txt
└── README.md
```

## 快速开始

### 环境要求
- Python 3.10+
- pip 或 uv

### 安装依赖

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 启动服务

```bash
# 开发模式
python -m app.main

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 访问文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 示例

### 用户注册
```bash
curl -X POST "http://localhost:8000/api/v1/users/register?username=test&password=test123"
```

### 登录获取 Token
```bash
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -d "username=test&password=test123"
```

### 买入股票
```bash
curl -X POST "http://localhost:8000/api/v1/trade/buy" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "000001", "quantity": 100, "price": "15.00"}'
```

### 创建价格提醒
```bash
curl -X POST "http://localhost:8000/api/v1/alerts" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001",
    "alert_name": "MA5突破提醒",
    "strategy_type": "MA",
    "strategy_config": {"period": 5, "direction": "up"},
    "notifier_type": "WEBSOCKET"
  }'
```

### 创建 AI 智能提醒
```bash
curl -X POST "http://localhost:8000/api/v1/alerts" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001",
    "alert_name": "AI智能提醒",
    "strategy_type": "MCP_SMART",
    "strategy_config": {
      "mcp_server": "my-server",
      "tool": "analyze_alert",
      "min_confidence": 0.7
    },
    "notifier_type": "MCP"
  }'
```

## 运行测试

```bash
pytest -v
```

## 配置说明

环境变量配置（可选）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接串 | `sqlite+aiosqlite:///./mock_stock.db` |
| `SECRET_KEY` | JWT 密钥 | 随机生成 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间 | 30 |

---

## 开发说明

本项目由 AI（Claude）辅助开发，用于探索 AI 在投资决策领域的应用能力。

## License

MIT License - 详见 [LICENSE](LICENSE) 文件