#!/usr/bin/env bash
# 修改代码后：停止旧 Bot → 跑测试 → 重启 Bot
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate

echo "==> 停止旧 Bot..."
pkill -f "python main.py -c config.yaml --bot" 2>/dev/null || true
sleep 1

echo "==> 运行测试..."
python -c "
from src.leg_parser import parse_spread_command
from src.query_service import SpreadQueryService

p = parse_spread_command('QQQ +1 730C, -1 750C, 60天')
assert len(p.legs) == 2
print('parser OK')

q = SpreadQueryService.from_config_file('config.yaml')
msg = q.handle_command('QQQ +1 730C, -1 750C, 60天')
assert '内在价值' in msg and '希腊值' in msg and '组合净希腊值' in msg
print('query OK (IV/greeks/intrinsic present)')
"

echo "==> 定时推送干跑..."
python main.py -c config.yaml --once --dry-run 2>/dev/null | grep -E "内在价值|希腊值|组合净希腊" | head -5

echo "==> 启动 Bot（后台）..."
nohup python main.py -c config.yaml --bot >> logs/bot.log 2>&1 &
echo $! > .bot.pid
sleep 2
if kill -0 "$(cat .bot.pid)" 2>/dev/null; then
  echo "Bot 已启动 PID=$(cat .bot.pid)"
  tail -3 logs/bot.log 2>/dev/null || true
else
  echo "Bot 启动失败" >&2
  exit 1
fi
