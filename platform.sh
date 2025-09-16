#!/bin/bash

# 智能代码安全分析平台管理脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 显示帮助信息
show_help() {
    echo "智能代码安全分析平台管理工具"
    echo ""
    echo "用法: $0 <命令> [选项]"
    echo ""
    echo "命令:"
    echo "  start     启动平台 (后台运行)"
    echo "  stop      停止平台"
    echo "  restart   重启平台"
    echo "  status    查看平台状态"
    echo "  logs      查看日志"
    echo ""
    echo "数据管理:"
    echo "  init      增量初始化（只添加新项目）"
    echo "  init-full 完整初始化（初始化+导入报告）"
    echo "  clean     清理不存在的项目"
    echo "  preview   预览初始化操作"
    echo "  fields    查看字段定义"
    echo ""
    echo "报告管理:"
    echo "  import    导入SARIF报告"
    echo "  import-preview  预览报告导入"
    echo "  import-force    强制重新导入报告"
    echo ""
    echo "登录管理:"
    echo "  login-disable    禁用登录功能（自动登录）"
    echo "  login-enable     启用登录功能"
    echo "  login-status     查看登录状态"
    echo ""
    echo "日志选项 (用于 logs 命令):"
    echo "  -f, --follow    实时跟踪日志"
    echo "  -n, --lines N   显示最后N行"
    echo "  -e, --error     只显示错误日志"
    echo "  -o, --output    只显示输出日志"
    echo ""
    echo "字段选项 (用于 fields 命令):"
    echo "  --model <name>  查看指定模型字段"
    echo "  --choices       查看选择项定义"
    echo "  --extensions    查看扩展建议"
    echo ""
    echo "示例:"
    echo "  $0 start                    # 启动平台"
    echo "  $0 login-disable            # 禁用登录（推荐）"
    echo "  $0 init-full                # 完整初始化（项目+报告导入）"
    echo "  $0 init                     # 增量初始化（只添加新项目）"
    echo "  $0 import                   # 导入所有SARIF报告"
    echo "  $0 import-preview           # 预览报告导入"
    echo "  $0 clean                    # 清理数据库中不存在的项目"
    echo "  $0 logs -f                  # 实时查看日志"
}

# 检查命令
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

COMMAND=$1
shift

case $COMMAND in
    start)
        "$SCRIPT_DIR/start_daemon.sh"
        ;;
    stop)
        "$SCRIPT_DIR/stop_daemon.sh"
        ;;
    restart)
        "$SCRIPT_DIR/restart_daemon.sh"
        ;;
    status)
        "$SCRIPT_DIR/status.sh"
        ;;
    logs)
        "$SCRIPT_DIR/logs.sh" "$@"
        ;;
    init)
        echo "=== 增量初始化部门和项目 ==="
        echo "只添加数据库中不存在的新项目"
        cd "$SCRIPT_DIR"
        source venv/bin/activate
        python manage.py auto_init
        ;;
    init-full)
        echo "=== 完整初始化（项目+报告导入） ==="
        echo "初始化项目并自动导入SARIF报告"
        cd "$SCRIPT_DIR"
        source venv/bin/activate
        python manage.py auto_init --import-reports
        ;;
    clean)
        echo "=== 清理数据库中不存在的项目 ==="
        echo "删除数据库中存在但文件系统中不存在的项目"
        cd "$SCRIPT_DIR"
        source venv/bin/activate
        python manage.py auto_init --clean
        ;;
    preview)
        echo "=== 预览初始化和清理操作 ==="
        echo "显示将要执行的操作，但不实际执行"
        cd "$SCRIPT_DIR"
        source venv/bin/activate
        python manage.py auto_init --clean --dry-run --import-reports
        ;;
    import)
        echo "=== 导入SARIF报告 ==="
        echo "扫描并导入所有SARIF报告文件"
        cd "$SCRIPT_DIR"
        source venv/bin/activate
        python manage.py import_reports
        ;;
    import-preview)
        echo "=== 预览SARIF报告导入 ==="
        echo "显示将要导入的报告，但不实际导入"
        cd "$SCRIPT_DIR"
        source venv/bin/activate
        python manage.py import_reports --dry-run
        ;;
    import-force)
        echo "=== 强制重新导入SARIF报告 ==="
        echo "删除已有漏洞，重新导入所有报告"
        cd "$SCRIPT_DIR"
        source venv/bin/activate
        python manage.py import_reports --force
        ;;
    fields)
        echo "=== 查看字段定义 ==="
        cd "$SCRIPT_DIR"
        source venv/bin/activate
        python manage.py show_fields "$@"
        ;;
    login-disable)
        echo "=== 禁用登录功能 ==="
        cd "$SCRIPT_DIR"
        source venv/bin/activate
        python manage.py toggle_login --disable
        ;;
    login-enable)
        echo "=== 启用登录功能 ==="
        cd "$SCRIPT_DIR"
        source venv/bin/activate
        python manage.py toggle_login --enable
        ;;
    login-status)
        echo "=== 查看登录状态 ==="
        cd "$SCRIPT_DIR"
        source venv/bin/activate
        python manage.py toggle_login --status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "未知命令: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac
