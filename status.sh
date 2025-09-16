#!/bin/bash

# 智能代码安全分析平台状态查看脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/platform.pid"
LOG_FILE="$SCRIPT_DIR/logs/platform.log"

echo "=== 智能代码安全分析平台状态 ==="

# 检查PID文件
if [ ! -f "$PID_FILE" ]; then
    echo "状态: ✗ 未运行 (无PID文件)"
    
    # 检查是否有遗留进程
    PIDS=$(pgrep -f "python.*manage.py.*runserver.*7000")
    if [ -n "$PIDS" ]; then
        echo "警告: 发现可能的遗留进程:"
        echo "$PIDS" | while read pid; do
            echo "  PID: $pid - $(ps -p $pid -o cmd --no-headers)"
        done
    fi
    exit 1
fi

# 读取PID
PID=$(cat "$PID_FILE")

# 检查进程状态
if ps -p $PID > /dev/null 2>&1; then
    echo "状态: ✓ 运行中"
    echo "PID: $PID"
    
    # 获取进程信息
    PROCESS_INFO=$(ps -p $PID -o pid,ppid,cmd,etime,pcpu,pmem --no-headers)
    echo "进程信息: $PROCESS_INFO"
    
    # 检查端口
    if netstat -tlnp 2>/dev/null | grep -q ":7000.*$PID/"; then
        echo "端口: ✓ 7000端口正在监听"
    else
        echo "端口: ✗ 7000端口未监听"
    fi
    
    # 检查服务响应
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:7000 | grep -q "200\|302"; then
        echo "服务: ✓ HTTP服务正常响应"
    else
        echo "服务: ✗ HTTP服务无响应"
    fi
    
    echo ""
    echo "访问地址:"
    echo "  主页: http://localhost:7000"
    echo "  管理界面: http://localhost:7000/admin"
    echo "  API文档: http://localhost:7000/api"
    
    # 显示最近日志
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "最近日志 (最后10行):"
        tail -n 10 "$LOG_FILE" | sed 's/^/  /'
    fi
    
else
    echo "状态: ✗ 进程不存在 (PID: $PID)"
    echo "清理PID文件..."
    rm -f "$PID_FILE"
    exit 1
fi
