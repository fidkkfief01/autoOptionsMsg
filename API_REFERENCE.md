# API 参考和快速查询指南

## 📚 模块 API 参考

### src.models - 数据模型

#### `OptionType` (Enum)
```python
from src.models import OptionType

# 可用值
OptionType.CALL = "call"
OptionType.PUT = "put"
```

#### `Side` (Enum)
```python
from src.models import Side

# 可用值
Side.LONG = "long"      # 买入头寸
Side.SHORT = "short"    # 卖出头寸
```

#### `OptionLeg` (数据类)
```python
from src.models import OptionLeg, OptionType, Side

leg = OptionLeg(
    underlying="QQQ",              # 标的代码 (自动大写)
    expiry="2026-06-26",           # 到期日期
    strike=730.0,                  # 行权价
    option_type=OptionType.CALL,   # 看涨/看跌
    side=Side.LONG,                # 买入/卖出
    quantity=1,                    # 数量 (>0)
    entry_price=5.50,              # 成本价 (>=0)
    manual_price=None              # 可选：手动报价
)
```

#### `OptionPortfolio` (组合容器)
```python
from src.models import OptionPortfolio

portfolio = OptionPortfolio(
    name="SPY 熊市看涨价差",
    multiplier=100,                # 合约乘数
    legs=[leg1, leg2, ...]         # 一个或多个腿
)
```

#### `PortfolioSnapshot` (快照结果)
```python
# 查询后获得
snapshot: PortfolioSnapshot = result

# 访问属性
print(f"初始成本: ${snapshot.cost}")
print(f"当前市值: ${snapshot.market_value}")
print(f"盈亏: ${snapshot.pnl}")
print(f"盈亏率: {snapshot.pnl_pct:.2%}")

# 访问详细报价
for leg_quote in snapshot.leg_quotes:
    print(f"{leg_quote.leg.underlying} {leg_quote.price}")
```

---

### src.service - 监控服务

#### `OptionsMonitorService`
```python
from src.service import OptionsMonitorService

# 方式 1：从配置文件加载
service = OptionsMonitorService.from_config_file("config.yaml")

# 方式 2：从配置对象初始化
from src.models import AppConfig
config = AppConfig(...)
service = OptionsMonitorService(config)

# 执行单次轮询
snapshots = service.poll_once(send_telegram=True)
# 返回值: list[PortfolioSnapshot]
```

**方法签名**：
```python
def poll_once(self, send_telegram: bool = True) -> list[PortfolioSnapshot]:
    """
    执行一次轮询循环
    
    参数:
        send_telegram: 是否发送 Telegram 通知 (默认 True)
    
    返回:
        所有组合的快照列表
    """
```

---

### src.query_service - 实时查询服务

#### `SpreadQueryService`
```python
from src.query_service import SpreadQueryService

# 初始化
service = SpreadQueryService.from_config_file("config.yaml")

# 处理用户查询
result = service.handle_command("QQQ +1 730C, -1 750C, 60天")
# 返回格式化的 HTML 字符串

print(result)  # 打印或通过 Telegram 发送
```

**方法签名**：
```python
def handle_command(self, text: str) -> str:
    """
    处理用户的期权查询指令
    
    参数:
        text: 用户输入 (例: "QQQ +1 730C, -1 750C, 60天")
    
    返回:
        HTML 格式的查询结果或错误消息
    """
```

---

### src.leg_parser - 腿解析器

#### `parse_spread_command`
```python
from src.leg_parser import parse_spread_command, LegParseError

try:
    parsed = parse_spread_command(
        "QQQ +1 730C, -1 750C, 60天",
        default_underlying="QQQ"
    )
    
    print(f"标的: {parsed.underlying}")
    print(f"腿数: {len(parsed.legs)}")
    print(f"目标 DTE: {parsed.target_dte}")
    
    for leg in parsed.legs:
        print(f"  {leg.side.value:5} {leg.quantity} {leg.strike} {leg.option_type.value}")
    
except LegParseError as e:
    print(f"解析错误: {e}")
```

**输入格式示例**：
```
QQQ +1 730C, -1 750C, 60天        # 完整格式
SPY +1 500C, -1 520C, 45d        # 45 天到期
+1 400P, -1 380P, 30天           # 省略标的，使用默认值
+2 100C, 60d                     # 单腿查询
```

---

### src.expiry_resolver - 到期日解析

#### `resolve_expiry`
```python
from src.expiry_resolver import resolve_expiry
from datetime import date

# 根据 DTE 查找最近的到期日
expiry_date = resolve_expiry(
    underlying="QQQ",     # 标的代码
    target_dte=60         # 目标天数
)
# 返回: "2026-06-26" (最接近 60 天的到期日)

# 计算实际 DTE
today = date.today()
actual_expiry = date.fromisoformat(expiry_date)
actual_dte = (actual_expiry - today).days
print(f"实际 DTE: {actual_dte} 天")
```

---

### src.pnl - 盈亏计算

#### `build_snapshot`
```python
from src.pnl import build_snapshot
from src.models import OptionPortfolio, LegQuote

# 输入组合和报价列表
snapshot = build_snapshot(portfolio, leg_quotes)

# 结果包含
print(f"成本: {snapshot.cost}")              # 初始投资
print(f"市值: {snapshot.market_value}")      # 当前价值
print(f"盈亏: {snapshot.pnl}")               # 绝对收益
print(f"收益率: {snapshot.pnl_pct * 100:.2f}%")  # 百分比收益
```

---

### src.underlying - 标的物查询

#### `fetch_underlying_mid`
```python
from src.underlying import fetch_underlying_mid

# 批量获取标的物中间价格
prices = fetch_underlying_mid(["QQQ", "SPY", "IWM"])
# 返回: {"QQQ": 445.67, "SPY": 580.23, "IWM": 195.45}

# 访问价格
qqq_price = prices.get("QQQ")
```

---

### src.providers - 数据提供商

#### 提供商接口
```python
from src.providers import QuoteProvider, AlpacaQuoteProvider, YFinanceQuoteProvider
from src.models import OptionPortfolio, LegQuote

# 创建提供商实例
alpaca_provider = AlpacaQuoteProvider(
    price_field="mid",      # bid | mid | ask
    feed="indicative"       # 可选参数
)

yfinance_provider = YFinanceQuoteProvider(
    price_field="mid"
)

# 查询组合
quotes: list[LegQuote] = provider.quote_portfolio(portfolio)

# 访问报价
for quote in quotes:
    print(f"{quote.leg.underlying} {quote.leg.strike}{quote.leg.option_type.value}")
    print(f"  价格: {quote.price}")
    print(f"  来源: {quote.source}")
    print(f"  时间: {quote.quoted_at}")
    if quote.greeks:
        print(f"  Delta: {quote.greeks.delta}")
```

---

### src.config_loader - 配置加载

#### `load_config`
```python
from src.config_loader import load_config
from src.models import AppConfig

# 从 YAML 文件加载
config: AppConfig = load_config("config.yaml")

# 访问配置
print(f"提供商: {config.provider}")
print(f"轮询间隔: {config.interval_seconds} 秒")
print(f"组合数: {len(config.portfolios)}")

for portfolio in config.portfolios:
    print(f"  - {portfolio.name}: {len(portfolio.legs)} 腿")
```

---

### src.telegram_bot - Telegram 机器人

#### `TelegramBotRunner`
```python
from src.telegram_bot import TelegramBotRunner
from src.query_service import SpreadQueryService

# 初始化机器人
query_service = SpreadQueryService.from_config_file("config.yaml")
bot = TelegramBotRunner(query_service)

# 启动机器人（在 main.py 中调用）
# bot.run()
```

**支持的命令**：
- `/start` - 显示欢迎和菜单
- `/help` - 显示使用说明
- `/query` - 显示查询示例
- `/menu` - 重新显示菜单

**键盘快捷按钮**：
```
📊 查询期权    ❓ 帮助
📝 示例        🔄 刷新菜单
```

---

## 🔧 常用命令参考

### 命令行操作

```bash
# 1. 仅查询，干运行（不发送 Telegram）
python main.py -c config.yaml --once --dry-run

# 2. 查询一次并发送 Telegram
python main.py -c config.yaml --once

# 3. 后台定时轮询
python main.py -c config.yaml

# 4. 启动 Telegram 交互机器人
python main.py -c config.yaml --bot

# 5. 帮助信息
python main.py -h
```

### 配置文件基本结构

```yaml
# 全局设置
interval_seconds: 300              # 轮询频率
notify_on_start: true              # 启动后立即执行

# 数据源配置
provider: alpaca                   # alpaca | yfinance | manual
price_field: mid                   # bid | mid | ask
alpaca_feed: indicative            # Alpaca 行情源

default_underlying: QQQ            # Telegram 机器人默认标的

# Telegram 配置
telegram:
  bot_token: ${TG_BOT_TOKEN}       # 从环境变量读取
  chat_id: ${TG_CHAT_ID}

# 监控的期权组合列表
portfolios:
  - name: "熊市看涨价差"
    multiplier: 100
    legs:
      - underlying: QQQ
        expiry: "2026-06-26"
        strike: 730
        option_type: call          # call | put
        side: long                 # long | short
        quantity: 1
        entry_price: 5.50
        manual_price: null         # 可选：覆盖自动价格
```

### 环境变量设置

```bash
# .env 文件内容
TG_BOT_TOKEN=your_bot_token_here
TG_CHAT_ID=your_chat_id_here

# Alpaca 信息（可选）
Key=your_alpaca_api_key
Secret=your_alpaca_secret
Endpoint=https://paper-trading.alpaca.markets
```

---

## 📊 期权查询语法速查表

### 基本格式

```
<标的> <腿1>, <腿2>, ..., <到期天数>
```

### 腿格式详解

```
<方向> <数量> <行权价><期权类型>

方向:       + (买入) 或 - (卖出)
数量:       正整数 (1, 2, 3, ...)
行权价:     浮点数 (无需加 $)
期权类型:   C/Call (看涨) 或 P/Put (看跌)
```

### 示例汇总

| 输入 | 说明 |
|------|------|
| `QQQ +1 730C, -1 750C, 60天` | QQQ 牛市看涨价差，60 DTE |
| `SPY +1 500C, -1 520C, 45d` | SPY 熊市看涨价差，45 DTE |
| `-1 400P, +1 380P, 60天` | 省略标的用默认值，看跌价差 |
| `+1 500C, 60天` | 单腿：买 500 看涨 |
| `+2 100C, -2 120C, 30d` | 多头价差，数量为 2 |

### 到期日表达方式

```
60天    ✓ 推荐
60d    ✓ 可用
60D    ✓ 可用
2026-06-26    ✗ 暂不支持（使用 DTE 代替）
```

---

## 🔍 消息格式示例

### 组合轮询输出示例

```
2026-05-28 14:30:45 [INFO] main: OptionsMonitorService 轮询完成
SPY 示例 | cost=150.00 mv=145.50 pnl=-4.50

Telegram 消息:

📈 期权组合报价

组合: SPY 示例
标的: SPY | 当前价: $580.23

├─ +1 500C @ $5.50 (Bid: $5.40, Ask: $5.60)
│  └─ Greeks: Δ=0.45, Γ=0.02, Θ=-0.05
│
└─ -1 520C @ $2.00 (Bid: $1.95, Ask: $2.05)
   └─ Greeks: Δ=-0.30, Γ=-0.01, Θ=+0.03

成本：-$150.00 (买入净支出)
市值：-$145.50
盈亏：-$4.50 (-3.00%)
```

### 查询命令输出示例

```
🔍 期权查询结果

标的: QQQ | 到期: 2026-06-26 | DTE: 60天
现价: $445.67

组合: QQQ 查询 (2026-06-26)
├─ +1 730C @ $0.05 (Bid: $0.03, Ask: $0.07)
├─ -1 750C @ $0.01 (Bid: $0.00, Ask: $0.02)
├─ 成本: -$4.00
├─ 市值: -$4.00
└─ 盈亏: $0.00 (0.00%)

📊 价差分析:
• 盈利区间: 730-750
• 最大收益: $4.00
• 最大亏损: $196.00
• ROI: 2.04%
```

---

## ⚠️ 常见错误代码和解决方案

### 配置错误

| 错误 | 原因 | 解决方案 |
|------|------|--------|
| `配置文件不存在` | config.yaml 未找到 | `cp config.example.yaml config.yaml` |
| `YAML 解析错误` | YAML 格式不正确 | 检查缩进和语法 |
| `字段验证失败` | 数据类型错误 | 检查配置中的字段类型 |
| `Telegram 错误` | Token 或 Chat ID 无效 | 验证环境变量设置 |

### 运行时错误

| 错误 | 原因 | 解决方案 |
|------|------|--------|
| `API 认证失败` | Alpaca Key/Secret 错误 | 验证 .env 文件 |
| `无法解析期权符号` | 行权价格式错误 | 使用标准数字格式 |
| `DTE 解析失败` | 到期日查询失败 | 检查标的是否有效 |
| `网络超时` | API 响应慢 | 检查网络连接或 API 限流 |

---

## 📈 盈亏计算示例

### 熊市看涨价差 (Bear Call Spread)

```
配置:
- +1 500C @ $5.50 (买入)
- -1 520C @ $2.00 (卖出)

成本计算:
净成本 = (5.50 - 2.00) × 100 = $350

当前报价:
- 500C 现价: $5.40
- 520C 现价: $2.05

市值计算:
现市值 = (5.40 - 2.05) × 100 = $335

盈亏:
PnL = $335 - $350 = -$15
PnL% = -15 / 350 = -4.29%

说明: 价差变窄，亏损 15 美元
```

### 牛市看涨价差 (Bull Call Spread)

```
配置:
- -1 100C @ $10.00 (卖出)
- +1 120C @ $5.00 (买入)

成本计算:
净成本 = (5.00 - 10.00) × 100 = -$500
(负数表示净收入)

当前报价:
- 100C 现价: $12.00
- 120C 现价: $4.00

市值计算:
现市值 = (4.00 - 12.00) × 100 = -$800

盈亏:
PnL = -$800 - (-$500) = -$300
PnL% = -300 / 500 = -60%

说明: 价差变宽，亏损 300 美元
```

---

**最后更新**: 2026 年 5 月 28 日
**文档版本**: 1.0

