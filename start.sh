#!/bin/bash

# 智能代码安全分析平台启动脚本

echo "=== 启动智能代码安全分析平台 ==="

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
python manage.py check --database default
if [ $? -ne 0 ]; then
    echo "✗ 数据库连接失败，请检查PostgreSQL服务和配置"
    exit 1
fi

# 应用数据库迁移
echo "应用数据库迁移..."
python manage.py migrate

# 启动开发服务器
echo "启动开发服务器..."
echo "访问地址: http://localhost:7000"
echo "管理界面: http://localhost:7000/admin"
echo "按 Ctrl+C 停止服务器"
echo ""

python manage.py runserver 0.0.0.0:7000
