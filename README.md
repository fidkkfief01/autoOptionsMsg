# autoOptionsMsg

定时查询美股期权组合价格、成本与盈亏，并通过 Telegram 推送。

## 你的 `.env` 配置

当前格式已支持：

```env
Key=...          # Alpaca API Key（已验证可用）
Secret=...       # Alpaca Secret
Endpoint=...     # Paper 交易地址（行情接口自动用 data.alpaca.markets）
```

另需补充 Telegram（否则只能 `--dry-run` 本地打印）：

```env
TG_BOT_TOKEN=...
TG_CHAT_ID=...
```

## 快速开始

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml   # 已生成 config.yaml 可直改
# 编辑 config.yaml 填入你的真实组合
python main.py -c config.yaml --once --dry-run   # 只查价不推送
python main.py -c config.yaml --once             # 查价并推送 TG
python main.py -c config.yaml                    # 定时轮询
python main.py -c config.yaml --bot              # Telegram 交互机器人
```

## Telegram 机器人（菜单 + 指令查询）

启动后向 Bot 发送价差指令，自动匹配到期日并返回报价分析：

```bash
python main.py -c config.yaml --bot
```

**输入示例：**

```
QQQ +1 730C, -1 750C, 60天
QQQ +1 730C,59天,-1 750C,307天
+1 740C, -1 760C, 45d
```

| 部分 | 含义 |
|------|------|
| `QQQ` | 标的（可省略，默认见 `default_underlying`） |
| `+1 730C` | 买入 1 张 730 看涨 |
| `-1 750C` | 卖出 1 张 750 看涨 |
| `60天` / `60d` | 目标到期天数（自动匹配最近标准到期日） |

到期天数放在最后表示所有腿使用同一到期日；也可以跟在每条腿后面，用于查询不同到期日组成的组合，例如 `QQQ +1 730C,59天,-1 750C,307天`。

Bot 命令：`/start` `/help` `/query` `/menu`，底部键盘有「查询期权 / 帮助 / 示例」。

## 行情源

| provider | 说明 |
|----------|------|
| `alpaca` | 默认，使用免费 **indicative** feed（约延迟 15 分钟） |
| `yfinance` | 无需 Key，但不稳定 |
| `manual` | 手动 `manual_price` |

`config.yaml` 中 `expiry` 须为真实存在的到期日（`YYYY-MM-DD`），`strike` 与 `option_type` 须与持仓一致。

## 盈亏公式

- 成本 = Σ (方向 × 建仓价 × 张数 × multiplier)
- 市值 = Σ (方向 × 现价 × 张数 × multiplier)
- 盈亏 = 市值 − 成本
