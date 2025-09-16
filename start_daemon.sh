#!/bin/bash

# 智能代码安全分析平台后台启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/platform.pid"
LOG_FILE="$SCRIPT_DIR/logs/platform.log"
ERROR_LOG="$SCRIPT_DIR/logs/platform_error.log"

# 确保日志目录存在
mkdir -p "$SCRIPT_DIR/logs"

echo "=== 智能代码安全分析平台后台启动 ==="

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "✗ 平台已在运行 (PID: $PID)"
        echo "如需重启，请先运行: ./stop_daemon.sh"
        exit 1
    else
        echo "清理旧的PID文件..."
        rm -f "$PID_FILE"
    fi
fi

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ 虚拟环境已激活"
else
    echo "✗ 虚拟环境不存在，请先运行 ./install.sh"
    exit 1
fi

# 检查数据库连接
echo "检查数据库连接..."
python manage.py check --database default > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "✗ 数据库连接失败，请检查PostgreSQL服务和配置"
    exit 1
fi

# 应用数据库迁移
echo "应用数据库迁移..."
python manage.py migrate > /dev/null 2>&1

# 收集静态文件
echo "收集静态文件..."
python manage.py collectstatic --noinput > /dev/null 2>&1

# 启动后台服务
echo "启动后台服务..."
nohup python manage.py runserver 0.0.0.0:7000 > "$LOG_FILE" 2> "$ERROR_LOG" &
SERVER_PID=$!

# 保存PID
echo $SERVER_PID > "$PID_FILE"

# 等待服务启动
sleep 3

# 检查服务是否成功启动
if ps -p $SERVER_PID > /dev/null 2>&1; then
    echo "✓ 平台已成功启动"
    echo "  PID: $SERVER_PID"
    echo "  访问地址: http://localhost:7000"
    echo "  管理界面: http://localhost:7000/admin"
    echo "  日志文件: $LOG_FILE"
    echo "  错误日志: $ERROR_LOG"
    echo ""
    echo "管理命令:"
    echo "  查看状态: ./status.sh"
    echo "  停止服务: ./stop_daemon.sh"
    echo "  重启服务: ./restart_daemon.sh"
    echo "  查看日志: ./logs.sh"
else
    echo "✗ 平台启动失败"
    rm -f "$PID_FILE"
    echo "请查看错误日志: $ERROR_LOG"
    exit 1
fi
