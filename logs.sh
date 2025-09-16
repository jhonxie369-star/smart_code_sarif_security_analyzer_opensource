#!/bin/bash

# 智能代码安全分析平台日志查看脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/platform.log"
ERROR_LOG="$SCRIPT_DIR/logs/platform_error.log"

# 解析命令行参数
FOLLOW=false
LINES=50
LOG_TYPE="all"

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -n|--lines)
            LINES="$2"
            shift 2
            ;;
        -e|--error)
            LOG_TYPE="error"
            shift
            ;;
        -o|--output)
            LOG_TYPE="output"
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  -f, --follow    实时跟踪日志"
            echo "  -n, --lines N   显示最后N行 (默认50)"
            echo "  -e, --error     只显示错误日志"
            echo "  -o, --output    只显示输出日志"
            echo "  -h, --help      显示帮助"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 -h 查看帮助"
            exit 1
            ;;
    esac
done

echo "=== 智能代码安全分析平台日志 ==="

case $LOG_TYPE in
    "error")
        if [ -f "$ERROR_LOG" ]; then
            echo "错误日志: $ERROR_LOG"
            echo "----------------------------------------"
            if [ "$FOLLOW" = true ]; then
                tail -f "$ERROR_LOG"
            else
                tail -n "$LINES" "$ERROR_LOG"
            fi
        else
            echo "错误日志文件不存在: $ERROR_LOG"
        fi
        ;;
    "output")
        if [ -f "$LOG_FILE" ]; then
            echo "输出日志: $LOG_FILE"
            echo "----------------------------------------"
            if [ "$FOLLOW" = true ]; then
                tail -f "$LOG_FILE"
            else
                tail -n "$LINES" "$LOG_FILE"
            fi
        else
            echo "输出日志文件不存在: $LOG_FILE"
        fi
        ;;
    "all")
        echo "日志文件位置:"
        echo "  输出日志: $LOG_FILE"
        echo "  错误日志: $ERROR_LOG"
        echo ""
        
        if [ "$FOLLOW" = true ]; then
            echo "实时跟踪所有日志 (Ctrl+C 退出):"
            echo "========================================"
            (
                if [ -f "$LOG_FILE" ]; then
                    tail -f "$LOG_FILE" | sed 's/^/[OUT] /' &
                fi
                if [ -f "$ERROR_LOG" ]; then
                    tail -f "$ERROR_LOG" | sed 's/^/[ERR] /' &
                fi
                wait
            )
        else
            if [ -f "$LOG_FILE" ]; then
                echo "输出日志 (最后 $LINES 行):"
                echo "----------------------------------------"
                tail -n "$LINES" "$LOG_FILE"
                echo ""
            fi
            
            if [ -f "$ERROR_LOG" ] && [ -s "$ERROR_LOG" ]; then
                echo "错误日志 (最后 $LINES 行):"
                echo "----------------------------------------"
                tail -n "$LINES" "$ERROR_LOG"
            else
                echo "无错误日志"
            fi
        fi
        ;;
esac
