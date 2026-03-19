# Mock Stock Trading Backend

> **⚠️ 本项目完全由 AI（Claude）实现，未经过任何人工代码编写。**

一个基于 FastAPI 的模拟炒股后端系统，支持股票交易、持仓管理、行情查询、量化指标计算和智能价格提醒等功能。

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

## 关于 AI 实现

本项目是 AI 模型的产物。整个开发过程

**无任何人工编写的代码。**

---

## License

MIT License - 详见 [LICENSE](LICENSE) 文件