#!/bin/bash

# 智能代码安全分析平台重启脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== 智能代码安全分析平台重启 ==="

# 停止服务
echo "正在停止服务..."
"$SCRIPT_DIR/stop_daemon.sh"

# 等待完全停止
sleep 2

# 启动服务
echo "正在启动服务..."
"$SCRIPT_DIR/start_daemon.sh"
