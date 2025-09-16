#!/bin/bash

# 智能代码安全分析平台停止脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/platform.pid"

echo "=== 智能代码安全分析平台停止 ==="

# 检查PID文件是否存在
if [ ! -f "$PID_FILE" ]; then
    echo "✗ 未找到PID文件，平台可能未运行"
    # 尝试查找并杀死可能的进程
    PIDS=$(pgrep -f "python.*manage.py.*runserver.*7000")
    if [ -n "$PIDS" ]; then
        echo "发现运行中的进程，正在停止..."
        echo "$PIDS" | xargs kill -TERM
        sleep 2
        echo "$PIDS" | xargs kill -KILL 2>/dev/null
        echo "✓ 已强制停止相关进程"
    fi
    exit 0
fi

# 读取PID
PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ! ps -p $PID > /dev/null 2>&1; then
    echo "✗ 进程 $PID 不存在，清理PID文件"
    rm -f "$PID_FILE"
    exit 0
fi

echo "正在停止平台 (PID: $PID)..."

# 优雅停止
kill -TERM $PID

# 等待进程结束
for i in {1..10}; do
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "✓ 平台已成功停止"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# 强制停止
echo "正在强制停止..."
kill -KILL $PID 2>/dev/null

# 再次检查
if ! ps -p $PID > /dev/null 2>&1; then
    echo "✓ 平台已强制停止"
    rm -f "$PID_FILE"
else
    echo "✗ 无法停止进程 $PID"
    exit 1
fi
