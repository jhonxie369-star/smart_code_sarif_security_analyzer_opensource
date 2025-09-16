#!/bin/bash

# 智能安全分析平台安装脚本

echo "=== 智能安全分析平台安装脚本 ==="

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python版本: $python_version"

# 创建虚拟环境
echo "创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 升级pip
echo "升级pip..."
pip install --upgrade pip

# 安装依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 安装翻译包
echo "安装翻译包..."
python3 -c "
import argostranslate.package
import argostranslate.translate

print('更新包索引...')
argostranslate.package.update_package_index()

print('获取可用包...')
available_packages = argostranslate.package.get_available_packages()

# 查找英文到中文的包
en_zh_package = next(
    filter(lambda x: x.from_code == 'en' and x.to_code == 'zh', available_packages),
    None
)

if en_zh_package:
    print(f'安装英中翻译包: {en_zh_package.from_code} -> {en_zh_package.to_code}')
    download_path = en_zh_package.download()
    argostranslate.package.install_from_path(download_path)
    print('✓ 翻译包安装成功')
else:
    print('✗ 未找到英中翻译包')
"

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p logs
mkdir -p media
mkdir -p staticfiles
mkdir -p templates

# 设置环境变量
echo "设置环境变量..."
cat > .env << EOF
# 数据库配置
DB_NAME=smart_security_analyzer
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# 报告路径配置
REPORT_BASE_PATH=/home/ubuntu/chaomeng/output
PROJECT_BASE_PATH=/home/ubuntu/chaomeng/project

# AI配置
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Django配置
DEBUG=True
SECRET_KEY=your-secret-key-here
EOF

# 数据库迁移
echo "执行数据库迁移..."
python manage.py makemigrations
python manage.py migrate

# 创建缓存表
echo "创建缓存表..."
python manage.py createcachetable

# 创建超级用户
echo "创建超级用户..."
echo "请按提示创建管理员账户："
python manage.py createsuperuser

# 收集静态文件
echo "收集静态文件..."
python manage.py collectstatic --noinput

echo "=== 安装完成 ==="
echo ""
echo "启动命令："
echo "  开发服务器: python manage.py runserver 0.0.0.0:7000"
echo ""
echo "访问地址："
echo "  Web界面: http://localhost:7000"
echo "  管理界面: http://localhost:7000/admin"
echo "  API文档: http://localhost:7000/api"
echo ""
echo "注意事项："
echo "1. 请确保PostgreSQL服务已启动"
echo "2. 请根据实际情况修改.env文件中的配置"
echo "3. 首次使用前请在管理界面创建部门和项目"
