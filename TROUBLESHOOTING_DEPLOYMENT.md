# 故障排查与部署指南

## 🔧 故障排查 (Troubleshooting)

### 1. 配置和启动问题

#### 问题 1.1：`ImportError: No module named 'src'`

**症状**：
```
Traceback:
  File "main.py", line X, in <module>
    from src.config_loader import load_config
ImportError: No module named 'src'
```

**原因分析**：
- Python 路径不正确
- 虚拟环境未激活
- 在错误的目录运行脚本

**解决方案**：
```bash
# 1. 确认当前目录
pwd  # 应该输出 /Users/feiye/Documents/autoOptionsMsg

# 2. 激活虚拟环境
source .venv/bin/activate

# 3. 确认 Python 路径
python -c "import sys; print(sys.path)"

# 4. 重新运行
python main.py -c config.yaml --once --dry-run
```

---

#### 问题 1.2：`FileNotFoundError: config.yaml`

**症状**：
```
配置文件不存在: config.yaml（可从 config.example.yaml 复制）
```

**原因分析**：
- 尚未创建 config.yaml
- 指定了错误的配置文件路径

**解决方案**：
```bash
# 方法 1：使用示例配置
cp config.example.yaml config.yaml

# 方法 2：编辑并验证
cat config.yaml  # 查看内容

# 方法 3：指定正确的路径
python main.py -c /path/to/config.yaml --once --dry-run
```

---

#### 问题 1.3：`yaml.YAMLError: mapping values are not allowed here`

**症状**：
```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**原因分析**：
- YAML 格式错误（通常是缩进问题）
- 特殊字符未正确转义

**验证和修复**：
```bash
# 1. 检查 YAML 语法
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# 2. 检查缩进（必须用空格，不能用 Tab）
cat -A config.yaml | head -20  # 查看特殊字符

# 3. 对比正确格式
diff config.yaml config.example.yaml
```

**YAML 格式检查清单**：
- [ ] 使用空格而非制表符
- [ ] 顶级键不缩进
- [ ] 列表项用 `-` 开头，后跟空格
- [ ] 嵌套内容缩进 2-4 个空格
- [ ] 字符串不需要引号（除非包含特殊字符）

---

### 2. 环境变量问题

#### 问题 2.1：`Telegram 通知失败 - 401 Unauthorized`

**症状**：
```
[ERROR] telegram_notifier: Telegram 认证失败: 401 Unauthorized
```

**原因分析**：
- `TG_BOT_TOKEN` 无效或过期
- 环境变量未正确读取

**调试步骤**：
```bash
# 1. 检查 .env 文件存在
ls -la .env

# 2. 验证环境变量加载
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('TG_BOT_TOKEN'))"

# 3. 验证 Token 格式
# 正确格式: 123456789:ABCdefGHIjklmnoPQRstuvwxyz-1234567890
echo $TG_BOT_TOKEN | head -c 20

# 4. 在 Telegram 中验证 Bot
# - 与 @BotFather 对话
# - 选择对应的 bot
# - 查看 token 是否匹配
```

**修复步骤**：
```bash
# 1. 获取新的 Bot Token
# a. 在 Telegram 中搜索 @BotFather
# b. 发送 /mybots
# c. 选择你的 bot
# d. 点击 "API Token"
# e. 复制 token

# 2. 更新 .env
cat > .env << EOF
TG_BOT_TOKEN=your_new_token_here
TG_CHAT_ID=your_chat_id_here
EOF

# 3. 重新启动应用
python main.py -c config.yaml --once --dry-run
```

---

#### 问题 2.2：`NameError: name 'telegram_bot_token' is not defined`

**症状**：
```
NameError: name 'telegram_bot_token' is not defined
```

**原因分析**：
- 环境变量未加载
- 函数调用时环境变量为 None

**解决方案**：
```bash
# 1. 确认 load_dotenv() 被调用
grep -n "load_dotenv" main.py

# 2. 检查 .env 文件路径
python -c "import os; from pathlib import Path; print(Path.cwd())"

# 3. 显式设置环境变量
export TG_BOT_TOKEN="123456789:ABCdefGHIjklmnoPQRstuvwxyz"
export TG_CHAT_ID="987654321"
python main.py -c config.yaml --once
```

---

### 3. API 和数据源问题

#### 问题 3.1：`Alpaca API 连接失败 - 401 Unauthorized`

**症状**：
```
[ERROR] alpaca_provider: API 认证失败: 401 Unauthorized
```

**原因分析**：
- API Key 或 Secret 无效
- Endpoint URL 错误
- 账户未激活

**调试和修复**：
```bash
# 1. 验证 Alpaca 凭证
echo "Key=$Key"
echo "Secret=$Secret"
echo "Endpoint=$Endpoint"

# 2. 测试 API 连接
python << 'EOF'
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('Key')
secret = os.getenv('Secret')
endpoint = os.getenv('Endpoint')

headers = {
    'APCA-API-KEY-ID': key,
    'Content-Type': 'application/json'
}

try:
    response = httpx.get(f"{endpoint}/v1/account", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
except Exception as e:
    print(f"错误: {e}")
EOF

# 3. 获取新的 API 密钥
# - 登录 https://app.alpaca.markets
# - 导航到 Settings → API Keys
# - 生成新的 API Key
# - 复制 Key 和 Secret 到 .env
```

**配置检查清单**：
- [ ] Endpoint 是否包含 `https://`
- [ ] Paper Trading Endpoint: `https://paper-trading.alpaca.markets`
- [ ] API Key 长度通常 > 20 字符
- [ ] Secret 长度通常 > 30 字符

---

#### 问题 3.2：`期权查询返回零价格或空结果`

**症状**：
```
LegQuote(price=0.0, source='alpaca')
```

**原因分析**：
- 期权链不存在（虚值过度或到期日太近/太远）
- 行权价不标准（不是 0.5 或 1 的倍数）
- 市场尚未开盘

**调试步骤**：
```bash
# 1. 检查当前时间和市场状态
python -c "from datetime import datetime; print(datetime.now())"

# 2. 测试行权价格
# 美股期权行权价通常：
# - 价格 < $100: 0.5 的倍数 (10, 10.5, 11, 11.5, ...)
# - 价格 > $100: 1 的倍数 (100, 101, 102, ...)

# 3. 查看可用到期日
python << 'EOF'
from src.expiry_resolver import resolve_expiry
# 尝试不同的 DTE
for dte in [30, 45, 60, 90, 180]:
    try:
        expiry = resolve_expiry("QQQ", dte)
        print(f"DTE {dte}: {expiry}")
    except Exception as e:
        print(f"DTE {dte}: Error - {e}")
EOF

# 4. 尝试 YFinance 作为备用源
# 在 config.yaml 中改为 provider: yfinance
```

**修复建议**：
```yaml
# config.yaml

# 检查这些字段
provider: yfinance        # 切换到 Yahoo Finance 测试
price_field: mid         # 尝试 bid 或 ask
default_underlying: SPY  # 尝试更流动的标的

# 修改到期日
expiry: "2026-06-19"     # 使用确认存在的到期日

# 调整行权价
strike: 500              # 确保是有效的行权价
```

---

### 4. 轮询和调度问题

#### 问题 4.1：`后台轮询进程挂起或消失`

**症状**：
- 启动了 `python main.py -c config.yaml`，但没有任何输出
- 进程在几分钟后自动退出

**原因分析**：
- 异常被静默捕获
- 输出被重定向
- 进程崩溃

**解决方案**：
```bash
# 1. 使用日志文件追踪
python main.py -c config.yaml 2>&1 | tee logs/app.log

# 2. 查看完整日志
tail -f logs/app.log

# 3. 检查错误
grep "ERROR\|EXCEPTION" logs/app.log

# 4. 以干运行模式测试
python main.py -c config.yaml --once --dry-run

# 5. 提高日志级别
# 在 main.py 中修改:
logging.basicConfig(level=logging.DEBUG)  # 改为 DEBUG
```

---

#### 问题 4.2：`轮询周期太长或太短`

**症状**：
- 轮询不按预期间隔执行
- API 限流告警

**原因分析**：
- `interval_seconds` 配置不当
- API 响应时间过长

**调整方案**：
```yaml
# config.yaml

# 推荐值
interval_seconds: 300   # 5 分钟 - 适合大多数场景
# interval_seconds: 600  # 10 分钟 - 保守方案
# interval_seconds: 60   # 1 分钟 - 仅用于测试

# 或根据标的流动性调整
# SPY: 60-120 秒
# QQQ: 120-180 秒
# 小市值股票: 300+ 秒
```

**监控 API 限流**：
```python
# 在日志中寻找
# [WARNING] provider: 接近 API 限流
# [ERROR] provider: 已触发限流，等待重试

# 解决方案：增加 interval_seconds
```

---

### 5. Telegram 机器人问题

#### 问题 5.1：`机器人无法识别命令`

**症状**：
- 输入命令后没有响应
- 收到错误消息

**原因分析**：
- Chat ID 不正确
- Bot 权限问题
- 输入格式错误

**诊断步骤**：
```bash
# 1. 验证 Chat ID
# 方法 1：通过机器人获取
# 启动 bot，发送 /start，查看日志中的 chat_id

# 方法 2：手动获取
# a. 添加 @userinfobot
# b. 将其添加到你的群组或私聊
# c. 它会返回你的 User ID

# 2. 验证机器人权限
# 在 @BotFather 中
# - 选择 bot
# - 点击 "Edit Bot"
# - 检查 "Inline mode" 是否启用

# 3. 测试消息格式
# 使用标准格式: "QQQ +1 730C, -1 750C, 60天"
```

**常见输入错误**：
```
❌ 错误                          ✓ 正确
QQQ 730C                         QQQ +1 730C, 60天
+730C                           +1 730C
730C, 750C, 60                  +1 730C, -1 750C, 60天
QQQ730                          QQQ +1 730C
```

---

#### 问题 5.2：`消息格式化错误或乱码`

**症状**：
- Telegram 消息显示 HTML 标签
- 价格信息显示不正确
- 表格错位

**原因分析**：
- 消息格式生成错误
- 特殊字符编码问题
- 数字格式不正确

**修复方案**：
```python
# 在 src/telegram_notifier.py 中检查

# 常见问题 1：缺少 parse_mode
# 修复：确保 parse_mode="HTML"

# 常见问题 2：特殊字符
# 修复：转义 HTML 字符
def escape_html(text):
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))

# 常见问题 3：数字格式
# 修复：使用格式化字符串
f"{price:,.2f}"  # 正确
f"{price}"       # 可能显示很长的小数
```

---

## 🚀 生产部署指南

### 部署前检查清单

```bash
# 1. 环境验证
[ ] Python >= 3.9
[ ] 虚拟环境已激活
[ ] 所有依赖已安装: pip list | grep -E "pydantic|httpx|apscheduler"

# 2. 配置验证
[ ] config.yaml 存在且有效
[ ] .env 文件存在（不在版本控制中）
[ ] 环境变量可正确加载

# 3. API 验证
[ ] Alpaca/YFinance 连接正常
[ ] Telegram Bot 令牌有效
[ ] Chat ID 正确

# 4. 功能测试
[ ] 干运行成功: python main.py --once --dry-run
[ ] 单次轮询成功: python main.py --once
[ ] 消息格式正确
```

---

### 部署方案 A：本地后台运行 (macOS)

#### 使用 `nohup`

```bash
# 1. 启动后台进程
nohup python main.py -c config.yaml > logs/app.log 2>&1 &

# 2. 获取进程 ID
ps aux | grep "python main.py"

# 3. 查看日志
tail -f logs/app.log

# 4. 停止进程
kill <PID>
```

#### 使用 `screen` 或 `tmux`

```bash
# 使用 screen
screen -S options-monitor
python main.py -c config.yaml
# Ctrl+A+D 分离

# 使用 tmux
tmux new-session -d -s options-monitor "python main.py -c config.yaml"
tmux attach-session -t options-monitor
```

---

### 部署方案 B：使用 systemd 服务 (Linux/Mac)

创建服务文件 `/etc/systemd/user/options-monitor.service`：

```ini
[Unit]
Description=Options Monitor Service
After=network.target

[Service]
Type=simple
User=feiye
WorkingDirectory=/Users/feiye/Documents/autoOptionsMsg
ExecStart=/Users/feiye/Documents/autoOptionsMsg/.venv/bin/python main.py -c config.yaml
Restart=always
RestartSec=300

[Install]
WantedBy=default.target
```

启用和运行：

```bash
# 重新加载 systemd 配置
systemctl --user daemon-reload

# 启用服务
systemctl --user enable options-monitor.service

# 启动服务
systemctl --user start options-monitor.service

# 查看状态
systemctl --user status options-monitor.service

# 查看日志
journalctl --user -u options-monitor.service -f
```

---

### 部署方案 C：Docker 容器化

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动应用
CMD ["python", "main.py", "-c", "config.yaml"]
```

构建和运行：

```bash
# 构建镜像
docker build -t options-monitor:latest .

# 运行容器（后台）
docker run -d \
  --name options-monitor \
  -v /path/to/config.yaml:/app/config.yaml \
  -v /path/to/.env:/app/.env \
  -v /path/to/logs:/app/logs \
  options-monitor:latest

# 查看日志
docker logs -f options-monitor

# 停止容器
docker stop options-monitor
```

`docker-compose.yml` 配置：

```yaml
version: '3.8'

services:
  options-monitor:
    build: .
    container_name: options-monitor
    restart: always
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./.env:/app/.env
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
```

运行：

```bash
docker-compose up -d
docker-compose logs -f
```

---

### 部署方案 D：云服务器部署 (AWS/DigitalOcean)

#### 初始设置

```bash
# 1. 连接到服务器
ssh user@your-server-ip

# 2. 更新系统
sudo apt update && sudo apt upgrade -y

# 3. 安装 Python 和依赖
sudo apt install -y python3.11 python3.11-venv python3-pip

# 4. 克隆项目
git clone <repo-url>
cd autoOptionsMsg

# 5. 创建虚拟环境
python3.11 -m venv .venv
source .venv/bin/activate

# 6. 安装依赖
pip install -r requirements.txt

# 7. 设置配置和环境变量
cp config.example.yaml config.yaml
# 编辑 config.yaml
nano .env  # 设置环境变量

# 8. 作为后台服务运行
nohup python main.py -c config.yaml > logs/app.log 2>&1 &
```

#### 使用 supervisor 进程管理

```bash
sudo apt install supervisor

sudo tee /etc/supervisor/conf.d/options-monitor.conf << EOF
[program:options-monitor]
directory=/home/user/autoOptionsMsg
command=/home/user/autoOptionsMsg/.venv/bin/python main.py -c config.yaml
autostart=true
autorestart=true
user=user
redirect_stderr=true
stdout_logfile=/home/user/autoOptionsMsg/logs/supervisor.log
EOF

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start options-monitor
```

---

### 监控和维护

#### 日志管理

```bash
# 定期备份日志
tar czf logs-$(date +%Y%m%d).tar.gz logs/

# 清理旧日志（保留 7 天）
find logs -name "*.log" -mtime +7 -delete

# 监控日志大小
du -sh logs/
```

#### 性能监控

```bash
# 监控进程资源使用
ps aux | grep "python main.py"

# 监控网络连接
lsof -i :8000  # 如果有 HTTP 接口

# 监控磁盘空间
df -h
```

#### 定期测试

```bash
# 每周运行干运行测试
0 2 * * 0 cd /path/to/autoOptionsMsg && \
  python main.py -c config.yaml --once --dry-run

# 监控日志文件大小
0 3 * * * tail -n 1000 logs/app.log > logs/app.log.tmp && \
  mv logs/app.log.tmp logs/app.log
```

---

## 📋 部署检查表

部署前必须完成的项目：

```
前期准备
- [ ] 项目代码已备份
- [ ] 配置文件已安全存储
- [ ] API 凭证已验证
- [ ] 虚拟环境已创建

功能测试
- [ ] 干运行测试通过
- [ ] 单次轮询成功
- [ ] Telegram 消息发送正常
- [ ] 错误处理正确

部署
- [ ] 选择部署方案
- [ ] 配置自动启动
- [ ] 配置日志轮转
- [ ] 配置监控告警

文档
- [ ] 部署步骤已记录
- [ ] 故障排查指南已保存
- [ ] 联系信息已更新
- [ ] 备份计划已制定
```

---

**文档版本**: 1.0  
**最后更新**: 2026 年 5 月 28 日

