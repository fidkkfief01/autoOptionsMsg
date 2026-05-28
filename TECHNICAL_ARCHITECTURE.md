# 技术架构与实现细节

## 📐 系统设计架构

### 分层架构模型

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Entry (main.py)              │
└───────────┬──────────────────────────────────────────────┬──┘
            │                                              │
    ┌───────▼─────┐                                  ┌─────▼────────┐
    │ Polling Mode│                                  │  Bot Mode    │
    │ (定时轮询)   │                                  │ (交互模式)   │
    └───────┬─────┘                                  └─────┬────────┘
            │                                              │
    ┌───────▼──────────────────────────────────────────────▼────────┐
    │              Business Logic Layer                              │
    │  ┌────────────────────┐  ┌──────────────────────────────────┐  │
    │  │ OptionsMonitorSvc  │  │    SpreadQueryService            │  │
    │  │ (poll_once)        │  │ (handle_command)                 │  │
    │  └────────────────────┘  └──────────────────────────────────┘  │
    │                    ▲              ▲                             │
    │                    └──────┬───────┘                             │
    └───────────────────────────┼─────────────────────────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │  Data Provider Layer    │
                    ├────────────────────────┤
                    │ • AlpacaProvider      │
                    │ • YFinanceProvider    │
                    │ • ManualProvider      │
                    └────────┬───────┬──────┘
                             │       │
        ┌────────────────────┘       └──────────────────────┐
        │                                                   │
    ┌───▼───────────┐                              ┌────────▼─────┐
    │ Alpaca API    │                              │ Yahoo Finance│
    │ (Real-time)   │                              │ API           │
    └───────────────┘                              └───────────────┘
```

### 核心工作流程

#### 1. 轮询模式流程图

```
启动应用
  │
  ├─ 加载配置 (config.yaml)
  │
  ├─ 初始化 OptionsMonitorService
  │
  ├─ 启动 BlockingScheduler
  │
  └─► 定时任务循环 (每 interval_seconds 秒)
      │
      ├─ 遍历每个 Portfolio
      │
      ├─ 调用 Provider.quote_portfolio()
      │  │
      │  ├─ 标准化期权符号 (OCC format)
      │  │
      │  └─ 批量查询行情数据
      │
      ├─ 调用 build_snapshot()
      │  │
      │  ├─ 计算总成本
      │  │
      │  ├─ 计算市场价值
      │  │
      │  └─ 计算盈亏
      │
      ├─ 获取标的物实时价格 (fetch_underlying_mid)
      │
      ├─ 格式化消息
      │
      ├─ 打印到控制台
      │
      └─ 发送 Telegram 通知
```

#### 2. Telegram Bot 查询流程

```
用户输入 "QQQ +1 730C, -1 750C, 60天"
  │
  ├─ parse_spread_command()
  │  │
  │  ├─ 解析标的 (QQQ)
  │  ├─ 解析腿 (+1 730C, -1 750C)
  │  └─ 解析到期 (60天)
  │
  ├─ resolve_expiry()
  │  │
  │  ├─ 获取目标 DTE (60 天)
  │  │
  │  └─ 查询最近的到期日 (2026-06-27)
  │
  ├─ 构建 OptionPortfolio
  │  │
  │  └─ 创建对应的 OptionLeg 列表
  │
  ├─ Provider.quote_portfolio()
  │  │
  │  └─ 实时查询四条腿的报价
  │
  ├─ build_snapshot()
  │  │
  │  └─ 计算价差成本和收益
  │
  ├─ 格式化为 HTML 消息
  │
  └─ 通过 TelegramNotifier 发送
```

---

## 🔄 数据模型关系图

```
OptionPortfolio
    │
    ├─ name: str
    ├─ multiplier: int (default=100)
    └─ legs: List[OptionLeg]
           │
           ├─ underlying: str
           ├─ expiry: str
           ├─ strike: float
           ├─ option_type: OptionType (CALL|PUT)
           ├─ side: Side (LONG|SHORT)
           ├─ quantity: int
           ├─ entry_price: float
           └─ manual_price: Optional[float]

PortfolioSnapshot
    │
    ├─ portfolio: OptionPortfolio
    ├─ leg_quotes: List[LegQuote]
    │              │
    │              ├─ leg: OptionLeg
    │              ├─ price: float
    │              ├─ source: str
    │              ├─ quoted_at: datetime
    │              ├─ intrinsic_value: Optional[float]
    │              ├─ time_value: Optional[float]
    │              ├─ implied_vol: Optional[float]
    │              └─ greeks: Optional[OptionGreeks]
    │                         │
    │                         ├─ delta: Optional[float]
    │                         ├─ gamma: Optional[float]
    │                         ├─ theta: Optional[float]
    │                         ├─ vega: Optional[float]
    │                         └─ rho: Optional[float]
    │
    ├─ cost: float (初始成本)
    ├─ market_value: float (当前市值)
    ├─ pnl: float (绝对盈亏)
    └─ pnl_pct: Optional[float] (百分比盈亏)
```

---

## 🛠 关键算法与逻辑

### 1. 盈亏计算公式 (PnL Calculation)

```python
# 单条腿的成本：
leg_cost = entry_price * quantity * multiplier * (-1 if side == LONG else 1)

# 组合总成本：
total_cost = sum(leg_cost for all legs)

# 单条腿的市值：
leg_market_value = current_price * quantity * multiplier * 
                   (-1 if side == LONG else 1)

# 组合市场价值：
total_market_value = sum(leg_market_value for all legs)

# 盈亏 (PnL)：
pnl = total_market_value - total_cost

# 盈亏百分比：
pnl_pct = (pnl / abs(total_cost)) * 100 if total_cost != 0 else None
```

### 2. 期权符号标准化 (OCC Symbol Standardization)

期权符号遵循 OCC (Options Clearing Corporation) 标准：

```
格式: {Underlying}{YY}{MM}{DD}{CallPut}{Strike}

示例：
- QQQ 期权于 2026-05-28，行权价 730，看涨
  → QQQ260528C00730000

字段说明：
- Underlying: 标的代码 (1-6 字符)
- YY: 到期年份 (2 位)
- MM: 到期月份 (2 位)
- DD: 到期日期 (2 位)
- CallPut: C (看涨) 或 P (看跌)
- Strike: 行权价 (8 位，含 3 位小数)
```

### 3. 到期日解析 (Expiry Resolution)

```python
# 输入: 目标 DTE (Days To Expiration)
# 输出: 实际到期日期

算法：
1. 从交易所获取所有可用的到期日期列表
2. 计算每个到期日与当前日期的差值
3. 找到 DTE 最接近的到期日（向后查找）
4. 返回该到期日期

# 示例：
当前日期: 2026-05-28
目标 DTE: 60 天
可用到期日: 2026-06-12, 2026-06-19, 2026-06-26, 2026-07-03, ...

实际 DTE: 
- 2026-06-12 → 15 天
- 2026-06-19 → 22 天
- 2026-06-26 → 29 天
- 2026-07-03 → 36 天
...

选择最接近 60 天的 → 需要查找表或 API
```

### 4. 腿解析器 (Leg Parser)

支持的输入格式：

```
基础格式: {Quantity} {Strike}{CallPut}

示例：
+1 730C      → 买入 1 张 730 看涨
-2 400P      # 卖出 2 张 400 看跌
+3 500C/500P → 可选的 Put 说明符

解析步骤：
1. 提取符号 (+/-) 确定方向
2. 提取数量 (正整数)
3. 提取行权价 (浮点数)
4. 提取期权类型 (C/Call, P/Put)

状态机：
初始状态 →  [符号] → [数量] → [行权价] → [期权类型] → 完成
```

---

## 📡 数据提供商接口设计

### QuoteProvider 基类

```python
class QuoteProvider(ABC):
    @abstractmethod
    def quote_portfolio(
        self, portfolio: OptionPortfolio
    ) -> list[LegQuote]:
        """
        查询组合中所有腿的报价
        
        返回:
            包含每条腿的报价和相关元数据的列表
        """
        pass
```

### Alpaca Provider 实现

```
请求流程：
1. 构建 OCC 格式的期权符号
2. 使用 httpx 调用 Alpaca REST API
3. 解析响应 JSON
4. 提取 bid/mid/ask 价格（根据配置）
5. 构建 LegQuote 对象

特点：
- 支持 real-time 和 indicative 行情源
- 需要 API Key 和 Secret
- 提供完整的 Greeks 数据
```

### Yahoo Finance Provider 实现

```
请求流程：
1. 构建 Yahoo Finance 格式的期权符号
2. 使用 yfinance 库查询
3. 解析期权链数据
4. 构建 LegQuote 对象

特点：
- 无需认证
- 免费使用
- 可能延迟 15-20 分钟
- Greeks 数据可能不完整
```

---

## 🔐 安全性考虑

### 1. 敏感信息管理

```
API Keys / Secrets / Tokens
    ↓
.env 文件 (gitignored)
    ↓
python-dotenv.load_dotenv()
    ↓
env_keys.py getter 函数
    ↓
运行时内存 (不持久化)
```

**最佳实践**：
- 环境变量通过 .env 文件存储
- .env 文件在 .gitignore 中
- 不在日志中打印敏感信息
- 配置文件使用 `${VAR_NAME}` 占位符

### 2. 输入验证

所有输入都通过 Pydantic 模型验证：

```python
# 示例：OptionLeg 的验证
underlying: str         # 自动转大写
expiry: str            # 日期格式检查
strike: float          # 非负数字
option_type: OptionType # 枚举验证
side: Side             # 枚举验证
quantity: int          # 正整数 (gt=0)
entry_price: float     # 非负数字 (ge=0)
```

### 3. 错误处理策略

```python
try:
    result = provider.quote_portfolio(portfolio)
except SpecificException as e:
    logger.exception("具体错误: %s", portfolio.name)
    # 错误恢复：使用缓存或默认值
except Exception as e:
    logger.exception("通用错误")
    # 记录但继续处理其他组合
```

---

## 🚀 性能优化

### 1. 批量查询优化

```python
# 而不是逐个查询每条腿
symbols = [leg.occ_symbol() for leg in portfolio.legs]
batch_quotes = provider.batch_quote(symbols)  # 一次 API 调用
```

### 2. 缓存策略

- 标的物价格：缓存 1-2 分钟
- 期权数据：基于配置的轮询间隔
- 到期日列表：缓存 1 小时

### 3. 网络优化

```python
# 使用 httpx 的连接池复用
client = httpx.Client()  # 保持连接活跃
response = client.get(url)
```

---

## 📊 日志系统

### 日志级别和用途

| 级别 | 场景 | 示例 |
|------|------|------|
| DEBUG | 开发调试 | 参数值、中间结果 |
| INFO | 正常流程 | 组合查询完成、消息发送 |
| WARNING | 可恢复问题 | 某个 API 调用失败 |
| ERROR | 严重错误 | 配置文件缺失、API 认证失败 |
| CRITICAL | 应用崩溃 | 无法继续运行 |

### 日志配置 (main.py)

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
```

---

## 🧪 测试策略

### 单元测试建议

```python
# test_models.py
def test_option_leg_validation():
    # 测试数据验证
    
# test_pnl.py
def test_snapshot_calculation():
    # 测试盈亏计算
    
# test_parser.py
def test_spread_command_parsing():
    # 测试命令解析
```

### 集成测试

```python
# test_integration.py
def test_polling_cycle():
    # 模拟完整轮询流程
    
def test_telegram_bot_command():
    # 测试 Telegram 交互
```

### 干运行 (Dry Run) 模式

```bash
python main.py --dry-run  # 不发送 Telegram
# 输出到控制台用于验证
```

---

## 🔄 扩展点 (Extension Points)

### 1. 自定义数据源

实现新的 `QuoteProvider` 子类：

```python
class CustomProvider(QuoteProvider):
    def quote_portfolio(self, portfolio: OptionPortfolio) -> list[LegQuote]:
        # 连接自定义数据源
        # 转换为 LegQuote 列表
        pass
```

### 2. 自定义通知渠道

扩展 `TelegramNotifier` 或创建新的通知器：

```python
class EmailNotifier(Notifier):
    def notify_snapshots(self, snapshots: list[PortfolioSnapshot]) -> None:
        # 通过 Email 发送
        pass
```

### 3. 自定义计算指标

在 `option_metrics.py` 中添加新的希腊字母或指标：

```python
def calculate_custom_metric(option: OptionLeg) -> float:
    # 自定义计算逻辑
    pass
```

---

## 📈 生产部署建议

### 1. 环境配置

```yaml
# 开发环境
provider: yfinance        # 免费测试
interval_seconds: 60      # 频繁更新

# 生产环境
provider: alpaca          # 生产数据源
interval_seconds: 300     # 5 分钟轮询
notify_on_start: false    # 不在启动时通知
```

### 2. 监控告警

- 监控轮询延迟和失败率
- API 限流告警
- Telegram 发送失败告警
- 日志中的异常关键词监测

### 3. 容器化部署 (Docker)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py", "-c", "config.yaml"]
```

---

**技术栈总结**：
- **语言**: Python 3.9+
- **调度**: APScheduler
- **数据验证**: Pydantic v2
- **HTTP 客户端**: httpx
- **配置**: PyYAML
- **环境管理**: python-dotenv
- **第三方 API**: Alpaca, Yahoo Finance, Telegram

