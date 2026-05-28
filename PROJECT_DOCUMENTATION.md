# autoOptionsMsg 项目文档

## 📋 项目概览

**项目名称**: autoOptionsMsg  
**项目描述**: 定时查询美股期权组合价格、成本与盈亏，并通过 Telegram 推送通知  
**主要功能**: 
- 定时轮询期权组合的实时价格和盈亏
- Telegram 交互式机器人查询期权价差
- 支持多个数据源（Alpaca、Yahoo Finance、手动输入）
- 灵活的配置管理和日志记录

---

## 🏗 项目架构

### 目录结构
```
autoOptionsMsg/
├── main.py                    # 应用入口
├── config.yaml               # 用户配置文件
├── config.example.yaml       # 配置文件示例
├── requirements.txt          # Python 依赖
├── README.md                 # 快速开始指南
├── logs/                     # 运行日志
├── scripts/                  # 辅助脚本
│   └── restart_and_test.sh  # 重启和测试脚本
└── src/                      # 核心源代码
    ├── __init__.py
    ├── models.py            # 数据模型定义
    ├── config_loader.py     # 配置加载器
    ├── service.py           # 监控服务
    ├── query_service.py     # 期权查询服务
    ├── telegram_bot.py      # Telegram 机器人
    ├── telegram_notifier.py # Telegram 通知器
    ├── pnl.py              # 盈亏计算
    ├── option_metrics.py    # 期权指标计算
    ├── underlying.py        # 标的物价格查询
    ├── leg_parser.py        # 期权腿解析
    ├── expiry_resolver.py   # 到期日解析
    ├── occ_symbol.py        # OCC 期权符号处理
    ├── env_keys.py          # 环境变量读取
    ├── spread_analytics.py  # 价差分析
    └── providers/           # 数据提供商
        ├── __init__.py
        ├── base.py          # 提供商基类
        ├── alpaca_provider.py     # Alpaca 数据源
        ├── yfinance_provider.py   # Yahoo Finance 数据源
        └── manual.py              # 手动输入数据源
```

---

## 🔑 核心模块说明

### 1. **Models** (`src/models.py`)
定义了应用中使用的所有数据模型：

| 模型 | 说明 |
|------|------|
| `OptionType` | 期权类型枚举（Call / Put） |
| `Side` | 头寸方向枚举（Long / Short） |
| `OptionLeg` | 单个期权腿（标的、到期日、行权价等） |
| `OptionPortfolio` | 期权组合（含多条腿） |
| `OptionGreeks` | 期权希腊字母（Delta、Gamma、Theta 等） |
| `LegQuote` | 期权腿报价（含价格、希腊字等） |
| `PortfolioSnapshot` | 组合快照（成本、市值、盈亏） |
| `AppConfig` | 应用配置（提供商、组合、Telegram 等） |

### 2. **Service** (`src/service.py`)
`OptionsMonitorService` 类负责核心监控流程：

```python
# 使用流程
service = OptionsMonitorService.from_config_file("config.yaml")
snapshots = service.poll_once(send_telegram=True)
```

**主要方法**:
- `poll_once(send_telegram)` - 执行一次轮询，查询所有组合并可选发送 Telegram 通知
- 自动处理多个组合的错误恢复
- 获取标的物实时价格用于盈亏计算

### 3. **Query Service** (`src/query_service.py`)
`SpreadQueryService` 类处理 Telegram 机器人的交互查询：

```python
# 处理用户输入
result = service.handle_command("QQQ +1 730C, -1 750C, 60天")
```

**功能**:
- 解析用户的期权指令（如 `+1 730C, -1 750C`）
- 自动匹配到期日
- 实时查询价格并计算盈亏

### 4. **数据提供商** (`src/providers/`)
支持多个数据源，通过 `QuoteProvider` 接口实现：

| 提供商 | 说明 | 优点 |
|-------|------|------|
| `AlpacaQuoteProvider` | Alpaca Paper Trading | 实时行情、官方数据 |
| `YFinanceQuoteProvider` | Yahoo Finance | 免费、无需密钥 |
| `ManualQuoteProvider` | 手动输入 | 测试和干运行 |

### 5. **Telegram Bot** (`src/telegram_bot.py`)
`TelegramBotRunner` 类实现交互式机器人：

**支持命令**:
- `/start` - 显示菜单
- `/help` - 显示输入格式说明
- `/query` - 期权查询示例
- `/menu` - 重新显示键盘菜单

**键盘菜单**:
```
📊 查询期权    ❓ 帮助
📝 示例        🔄 刷新菜单
```

### 6. **盈亏计算** (`src/pnl.py`)
`build_snapshot()` 函数计算组合的成本、市值和盈亏：

```python
snapshot = build_snapshot(portfolio, leg_quotes)
# 结果包含:
# - cost: 初始成本
# - market_value: 当前市值
# - pnl: 绝对盈亏
# - pnl_pct: 盈亏百分比
```

### 7. **其他关键模块**

| 模块 | 功能 |
|------|------|
| `leg_parser.py` | 解析用户输入的期权腿格式 |
| `expiry_resolver.py` | 根据天数找到最近的到期日 |
| `underlying.py` | 获取标的物的实时中间价格 |
| `option_metrics.py` | 计算期权的 Greeks 和其他指标 |
| `occ_symbol.py` | 处理 OCC 期权符号标准化 |
| `config_loader.py` | 加载和验证 YAML 配置文件 |
| `env_keys.py` | 从环境变量读取敏感信息 |

---

## ⚙️ 配置说明

### 环境变量 (`.env` 文件)

```env
# Alpaca API（可选，需要时填充）
Key=<your_alpaca_api_key>
Secret=<your_alpaca_secret>
Endpoint=https://paper-trading.alpaca.markets

# Telegram（必需，除非仅进行 --dry-run）
TG_BOT_TOKEN=<your_telegram_bot_token>
TG_CHAT_ID=<your_chat_id>
```

### YAML 配置 (`config.yaml`)

```yaml
interval_seconds: 300              # 轮询间隔（秒）
notify_on_start: true              # 启动时是否立即通知

provider: alpaca                   # 数据源：alpaca | yfinance | manual
price_field: mid                   # 价格字段：bid | mid | ask
alpaca_feed: indicative            # Alpaca 行情类型

default_underlying: QQQ            # 默认标的

telegram:
  bot_token: ${TG_BOT_TOKEN}       # 从环境变量读取
  chat_id: ${TG_CHAT_ID}

portfolios:                        # 监控的组合列表
  - name: "SPY 示例"
    multiplier: 100                # 合约乘数
    legs:                          # 期权腿
      - underlying: SPY
        expiry: "2026-05-28"
        strike: 500
        option_type: call
        side: long
        quantity: 1
        entry_price: 10.00
        manual_price: null         # 可选：手动覆盖价格
```

---

## 🚀 使用指南

### 1. 快速开始

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制配置文件
cp config.example.yaml config.yaml

# 编辑配置
# - 填入你的组合信息
# - 设置环境变量 TG_BOT_TOKEN 和 TG_CHAT_ID
```

### 2. 三种运行模式

#### 模式 A：干运行（仅查询，不发送 Telegram）
```bash
python main.py -c config.yaml --once --dry-run
```
输出到控制台，适合测试配置。

#### 模式 B：一次查询并推送
```bash
python main.py -c config.yaml --once
```
执行一次完整的查询和通知流程。

#### 模式 C：后台定时轮询
```bash
python main.py -c config.yaml
```
按 `interval_seconds` 定期轮询并推送。

#### 模式 D：Telegram 交互机器人
```bash
python main.py -c config.yaml --bot
```
启动交互式机器人，接收用户指令实时查询。

### 3. Telegram 机器人使用示例

**输入格式**:
```
<标的> <腿1>, <腿2>, ..., <到期天数>
```

**完整示例**:
```
QQQ +1 730C, -1 750C, 60天        # 730看涨买1张，750看涨卖1张
SPY +1 580C, -1 600C, 45d        # SPY 行权价范围
+1 740C, -1 760C, 60天           # 省略标的，自动用默认值(QQQ)
```

**机器人返回结果示例**:
```
🔍 查询结果

标的: QQQ | 到期: 2026-06-27 | DTE: 60天
现价: $445.67

组合: QQQ 查询 (2026-06-27)
├─ +1 730C @ $0.05 (Bid: $0.03, Ask: $0.07)
├─ -1 750C @ $0.01 (Bid: $0.00, Ask: $0.02)
├─ 成本: -$4.00
├─ 市值: -$4.00
└─ 盈亏: $0.00 (0.00%)
```

---

## 📊 数据流向

```
用户配置 (config.yaml)
    ↓
应用启动 (main.py)
    ↓
配置加载器 (config_loader.py)
    ↓
监控服务 (OptionsMonitorService)
    ↓
数据提供商 (Alpaca/YFinance)
    ↓
腿解析 + 期权标准化
    ↓
盈亏计算 (PnL Calculator)
    ↓
Telegram 通知 + 本地日志
```

---

## 🔌 外部依赖

| 包 | 版本 | 用途 |
|---|------|------|
| `apscheduler` | >=3.10.4 | 定时调度 |
| `httpx` | >=0.27.0 | HTTP 请求 |
| `pydantic` | >=2.7.0 | 数据验证 |
| `pyyaml` | >=6.0.1 | YAML 解析 |
| `python-dotenv` | >=1.0.1 | 环境变量加载 |
| `yfinance` | >=0.2.54 | Yahoo Finance API |

---

## 🛠 开发指南

### 添加新的数据提供商

1. 在 `src/providers/` 下创建新文件（如 `new_provider.py`）
2. 继承 `QuoteProvider` 基类
3. 实现 `quote_portfolio()` 方法
4. 在 `service.py` 的 `_build_provider()` 中添加实例化逻辑

### 扩展 Telegram 机器人功能

1. 在 `telegram_bot.py` 中添加新的消息处理逻辑
2. 利用现有的 `SpreadQueryService` 进行查询
3. 格式化响应消息并通过 `TelegramNotifier` 发送

### 自定义盈亏计算

1. 修改 `src/pnl.py` 的计算逻辑
2. 调整 `build_snapshot()` 的返回值
3. 更新相关的单元测试

---

## 📝 重要提示

### 环境变量安全
- **不要** 将 `.env` 文件提交到版本控制
- 使用 `python-dotenv` 安全加载敏感信息
- 在 `env_keys.py` 中定义的 getter 会在运行时读取变量

### 配置文件管理
- `config.example.yaml` 是模板，不包含真实数据
- `config.yaml` 是用户配置，应该在 `.gitignore` 中
- 支持环境变量替换：`${VAR_NAME}` 自动读取

### 定时轮询
- `interval_seconds` 建议设置为 300-600 秒（5-10 分钟）
- 避免过于频繁的查询以减少 API 调用和资源消耗
- 查询失败会被捕获并记录，但不会中断轮询循环

### Telegram 限制
- 确保 `TG_BOT_TOKEN` 和 `TG_CHAT_ID` 正确配置
- Bot 需要有发送消息的权限
- 消息格式支持 HTML 标签（`<b>`、`<i>` 等）

---

## 🐛 常见问题

### 1. 配置文件不存在错误
```
配置文件不存在: config.yaml（可从 config.example.yaml 复制）
```
**解决**: 运行 `cp config.example.yaml config.yaml` 后编辑

### 2. 环境变量未读取
确保：
- `.env` 文件在项目根目录
- 使用 `load_dotenv()` 加载（main.py 已包含）
- 变量名匹配（区分大小写）

### 3. Alpaca API 连接失败
检查：
- API Key 和 Secret 是否正确
- Endpoint 是否正确（paper trading: `https://paper-trading.alpaca.markets`）
- 网络连接是否正常

### 4. 期权查询返回零价格
原因：
- 到期日太远或太近（可能无活跃期权）
- 行权价过度虚值
- 数据源暂时无数据

---

## 📧 联系与支持

- 项目文档: 见 README.md
- 配置示例: 见 config.example.yaml
- 快速命令参考:
  ```bash
  python main.py -c config.yaml --once --dry-run   # 测试
  python main.py -c config.yaml --once             # 运行一次
  python main.py -c config.yaml                    # 后台运行
  python main.py -c config.yaml --bot              # 启动机器人
  ```

---

**文档生成时间**: 2026年5月28日  
**最后更新**: 当前项目版本
