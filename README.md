# Mock Stock Trading Backend

> **免责声明：本项目仅供学习和研究目的，不构成任何投资建议。**

一个用于测试 AI 投资决策效果的模拟炒股后端系统。

---

## 为什么做这个

**核心问题：AI 给出的投资建议，能不能赚钱？**

传统量化策略用固定规则判断买卖信号：

```
RSI > 70 → 超买，卖出
MA5 上穿 MA20 → 金叉，买入
```

但市场是复杂的，指标经常矛盾。本项目让 LLM 做综合判断：

```
输入：MA + RSI + MACD + 持仓盈亏 + 新闻
输出：综合考虑后的买卖建议 + 理由
```

目标：验证 **LLM + 量化指标** 是否比单纯的技术指标策略更有效。

---

## 怎么用

### 核心设计：策略器 + 执行器

**策略器**：判断是否触发，返回 true/false + 建议操作（买入/卖出/观望）

**执行器**：执行触发后的动作（自动交易 / 发送通知）

### 组合使用

| 策略器 | 执行器 | 场景 |
|--------|--------|------|
| 传统量化（MA/RSI） | 自动交易执行器 | 传统量化自动交易 |
| AI 智能策略 | 自动交易执行器 | AI 自动模拟交易 |
| AI 智能策略 | 通知执行器 | AI 建议，人工执行 |
| 传统量化 | 通知执行器 | 传统量化信号提醒 |

### 流程示意

**AI 自动模拟交易**

```
行情数据 + 持仓信息 + 量化指标
         ↓
    AI 策略器判断
         ↓
    返回"买入"建议
         ↓
   自动交易执行器调用 API
         ↓
   更新持仓，等待下次决策
```

**AI 建议 + 人工执行**

```
行情数据 + 持仓信息 + 量化指标
         ↓
    AI 策略器判断
         ↓
    返回"买入"建议
         ↓
   通知执行器推送给用户
         ↓
   用户在真实市场交易
         ↓
   用户调用 API 记录结果
         ↓
   AI 基于真实持仓做下次决策
```

### 关键设计

| 设计 | 原因 |
|------|------|
| 策略器只判断，不执行 | 职责分离，AI 不需要知道交易 API |
| 执行器负责具体动作 | 灵活组合，任意策略 + 任意执行器 |
| 价格可自定义 | 记录真实成交价，确保持仓成本准确 |

---

## Q&A

**Q: 这和传统量化有什么区别？**

传统量化用固定规则，本项目用 LLM 做综合判断。比如：
- 传统：RSI > 70 → 卖
- 本项目：RSI > 70，但 MACD 金叉，你已盈利 20%，新闻偏利好 → 建议减仓观望

**Q: AI 策略器为什么不直接调用交易 API？**

职责分离：
- 策略器只做判断，返回建议
- 执行器负责具体动作

这样 AI 不需要了解交易 API，也方便组合使用（同一个 AI 策略可以搭配自动执行器或通知执行器）。

---

## 技术实现

### 功能特性

- **用户系统**：注册登录、账户余额管理
- **交易系统**：买入卖出、持仓成本计算、交易历史
- **行情系统**：实时行情（akshare）、持仓市值与盈亏
- **量化指标**：MA、EMA、MACD、RSI、布林带
- **提醒系统**：策略器（阈值/均线/MACD/RSI/AI智能）+ 执行器（自动交易/通知）

### 技术栈

FastAPI + SQLite + SQLAlchemy + akshare + APScheduler

### 项目结构

```
app/
├── api/          # API 路由
├── models/       # 数据模型
├── schemas/      # Pydantic 模式
├── services/     # 业务逻辑
├── strategies/   # 策略器（含 AI 智能策略）
├── executors/    # 执行器（自动交易/通知）
├── quant/        # 量化指标计算
├── quote/        # 行情数据源
└── db/           # 数据库配置
```

### API 接口

| 模块 | 接口 | 说明 |
|------|------|------|
| 用户 | `POST /users/register` | 注册 |
| | `POST /users/login` | 登录 |
| 交易 | `POST /trade/buy` | 买入 |
| | `POST /trade/sell` | 卖出 |
| | `GET /trade/history` | 交易历史 |
| 持仓 | `GET /positions` | 持仓列表 |
| 资产 | `GET /portfolio/total` | 总资产 |
| | `GET /portfolio/profit-loss` | 盈亏情况 |
| 行情 | `GET /quote/{stock_code}` | 实时行情 |
| 提醒 | `POST /alerts` | 创建提醒 |
| | `POST /alerts/{id}/check` | 手动检查 |

完整 API 文档：启动后访问 http://localhost:8000/docs

---

## 快速开始

### 安装

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 启动

```bash
uvicorn app.main:app --reload --port 8000
```

### 示例：创建 AI 智能提醒

**AI 自动交易**

```bash
curl -X POST "http://localhost:8000/api/v1/alerts" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001",
    "alert_name": "AI自动交易",
    "strategy_type": "MCP_SMART",
    "strategy_config": {
      "mcp_server": "my-server",
      "tool": "analyze_alert"
    },
    "executor_type": "AUTO_TRADE"
  }'
```

**AI 建议 + 人工执行**

```bash
curl -X POST "http://localhost:8000/api/v1/alerts" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001",
    "alert_name": "AI建议提醒",
    "strategy_type": "MCP_SMART",
    "strategy_config": {
      "mcp_server": "my-server",
      "tool": "analyze_alert"
    },
    "executor_type": "WEBSOCKET"
  }'
```

---

## 开发进度

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 1 | 项目初始化、数据库模型 | ✅ |
| Phase 2 | 用户 API、持仓 API | ✅ |
| Phase 3 | 交易 API、行情 API | ✅ |
| Phase 4 | 提醒系统、量化指标 | ✅ |
| Phase 5 | 定时任务 | 待开发 |
| Phase 6 | WebSocket 实时推送 | 待开发 |

---

## License

MIT License