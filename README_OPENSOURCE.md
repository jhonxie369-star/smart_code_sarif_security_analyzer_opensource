# 智能代码安全分析平台 (开源版)

基于Django和DefectDojo架构设计的现代化代码安全漏洞管理平台，集成AI分析能力和自动扫描功能。

## 🚀 功能特性

### 核心功能
- **自动扫描**: 支持CodeQL、Semgrep等多种扫描工具
- **智能队列**: 扫描任务自动排队，避免资源冲突
- **报告解析**: 自动解析SARIF格式报告
- **漏洞管理**: 完整的漏洞生命周期管理
- **统计分析**: 丰富的安全统计和报告功能

### AI增强功能 (可选)
- **智能分析**: 支持多种AI服务接入进行漏洞分析
- **自动翻译**: 支持多种翻译服务的漏洞信息翻译
- **风险评估**: AI辅助的风险评估和修复建议

## 📁 目录结构

```
smart_security_analyzer/
├── workspace/                 # 工作空间目录
│   ├── scan_temp/            # 扫描临时文件
│   ├── reports/              # 扫描报告输出
│   └── projects/             # 项目源码存储
├── tools/                    # 扫描工具目录
│   ├── codeql/              # CodeQL扫描工具 (需自行安装)
│   ├── codeql-rules/        # CodeQL扫描规则 (需自行安装)
│   └── jdk/                 # JDK工具 (需自行安装)
├── logs/                    # 日志文件
├── static/                  # 静态文件
├── templates/               # 模板文件
├── core/                    # 核心应用
├── api/                     # API应用
├── parsers/                 # 解析器
├── ai_analysis/             # AI分析 (可选)
├── translation/             # 翻译服务 (可选)
└── statistics/              # 统计服务
```

## 🛠️ 安装部署

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd smart_security_analyzer

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装基础依赖
pip install -r requirements.txt
```

### 2. 扫描工具安装

#### CodeQL 安装
```bash
# 创建工具目录
mkdir -p tools/codeql tools/codeql-rules

# 下载 CodeQL CLI
# 访问 https://github.com/github/codeql-cli-binaries/releases
# 下载适合你系统的版本到 tools/codeql/ 目录

# 下载 CodeQL 查询规则
# 访问 https://github.com/github/codeql
# 下载或克隆到 tools/codeql-rules/ 目录
```

#### Semgrep 安装
```bash
# 安装 Semgrep
pip install semgrep
```

#### JDK 安装
```bash
# 创建 JDK 软链接 (用于 Java 项目编译)
# 方法1: 软链接到系统JDK
ln -s /usr/lib/jvm/java-11-openjdk-amd64 tools/jdk

# 方法2: 下载并解压JDK到 tools/jdk/ 目录
```

### 3. 数据库配置

```bash
# 安装 PostgreSQL (推荐)
sudo apt-get install postgresql postgresql-contrib

# 创建数据库
sudo -u postgres createdb smart_security_analyzer

# 创建数据库用户
sudo -u postgres psql -c "CREATE USER analyzer WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE smart_security_analyzer TO analyzer;"
```

### 4. 环境配置

复制并编辑环境配置文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# 数据库配置
DB_NAME=smart_security_analyzer
DB_USER=analyzer
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# 扫描配置
AUTO_SCAN_ENABLED=True
SCAN_TIMEOUT=3600

# 登录配置 (开发环境可禁用登录)
DISABLE_LOGIN=True
AUTO_LOGIN_USER=admin

# AI分析配置 (可选)
# 如需启用AI分析，请配置以下选项之一：

# OpenAI配置
# AI_PROVIDER=openai
# OPENAI_API_KEY=your-openai-api-key
# OPENAI_MODEL=gpt-3.5-turbo

# Azure OpenAI配置
# AI_PROVIDER=azure
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_KEY=your-azure-key
# AZURE_OPENAI_VERSION=2023-05-15
# AZURE_DEPLOYMENT_NAME=your-deployment-name

# 自定义API配置
# AI_PROVIDER=custom
# CUSTOM_API_URL=https://your-api-endpoint.com/chat
# CUSTOM_API_KEY=your-api-key
```

### 5. 初始化应用

```bash
# 运行数据库迁移
python manage.py migrate

# 创建缓存表
python manage.py createcachetable

# 创建超级用户
python manage.py createsuperuser

# 收集静态文件
python manage.py collectstatic
```

### 6. 启动服务

```bash
# 开发环境
python manage.py runserver 0.0.0.0:7000

# 生产环境
pip install gunicorn
gunicorn smart_security_analyzer.wsgi:application --bind 0.0.0.0:7000
```

## 🎯 功能使用

### 1. 快速扫描
- 访问: `http://localhost:7000/api/quick-scan/`
- 输入Git仓库地址进行自动扫描
- 支持自动语言检测和工具选择

### 2. 任务监控
- 访问: `http://localhost:7000/api/task-monitor/`
- 查看所有扫描任务状态
- 支持任务终止和日志查看

### 3. 错误日志
- 访问: `http://localhost:7000/api/error-logs/`
- 实时查看平台运行日志
- 支持级别过滤和日志清空

### 4. 管理界面
- 访问: `http://localhost:7000/admin/`
- 管理项目、部门、漏洞等数据
- 查看统计报告和分析结果

## 🔧 AI功能配置

### AI分析功能

平台支持多种AI服务进行漏洞分析：

#### 1. OpenAI 配置
```bash
# 安装依赖
pip install openai

# 环境变量配置
AI_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo
```

#### 2. Azure OpenAI 配置
```bash
# 安装依赖
pip install openai

# 环境变量配置
AI_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-azure-key
AZURE_OPENAI_VERSION=2023-05-15
AZURE_DEPLOYMENT_NAME=your-deployment-name
```

#### 3. 自定义API配置
```bash
# 环境变量配置
AI_PROVIDER=custom
CUSTOM_API_URL=https://your-api-endpoint.com/chat
CUSTOM_API_KEY=your-api-key
```

### 翻译功能

平台支持多种翻译服务：

#### 1. Google翻译 (免费)
```bash
# 安装依赖
pip install googletrans==4.0.0rc1

# 环境变量配置
TRANSLATION_PROVIDER=google
```

#### 2. 百度翻译
```bash
# 环境变量配置
TRANSLATION_PROVIDER=baidu
BAIDU_APP_ID=your-baidu-app-id
BAIDU_SECRET_KEY=your-baidu-secret-key
```

#### 3. 本地翻译模型
```bash
# 安装依赖
pip install transformers torch

# 环境变量配置
TRANSLATION_PROVIDER=local
```

## 📝 API接口

### 扫描相关
- `POST /api/v1/projects/{id}/auto_scan/` - 自动扫描项目
- `GET /api/v1/scans/` - 获取扫描任务列表
- `POST /api/v1/scans/{id}/kill_task/` - 终止扫描任务
- `GET /api/v1/scans/{id}/logs/` - 获取扫描日志

### AI分析相关 (需配置AI服务)
- `POST /api/v1/findings/{id}/ai_analysis/` - AI分析单个漏洞
- `POST /api/v1/findings/batch_ai_analysis/` - 批量AI分析

### 翻译相关 (需配置翻译服务)
- `POST /api/v1/findings/{id}/translate/` - 翻译漏洞信息

### 队列管理
- `GET /api/v1/statistics/queue_status/` - 获取队列状态

## 🚨 注意事项

### 扫描工具配置
1. **CodeQL**: 需要手动下载CLI和查询规则
2. **Semgrep**: 通过pip安装即可
3. **JDK**: Java项目扫描需要JDK环境

### AI功能配置
1. **OpenAI**: 需要有效的API密钥
2. **Azure OpenAI**: 需要Azure订阅和部署
3. **自定义API**: 需要兼容的API接口

### 翻译功能配置
1. **Google翻译**: 免费但可能不稳定
2. **百度翻译**: 需要注册开发者账号
3. **本地模型**: 需要下载模型文件，占用存储空间

### 性能优化
1. 扫描任务会自动排队，避免并发冲突
2. 大型项目建议增加超时时间配置
3. 定期清理临时文件和日志

### 安全建议
1. 生产环境设置 `DEBUG=False`
2. 配置适当的 `ALLOWED_HOSTS`
3. 使用HTTPS并设置安全Cookie
4. 定期更新扫描工具版本

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 常见问题

### Q: CodeQL扫描失败怎么办？
A: 检查CodeQL CLI是否正确安装，查询规则是否下载完整，JDK环境是否配置正确。

### Q: AI分析功能无法使用？
A: 确认已安装相应的Python库，API密钥配置正确，网络连接正常。

### Q: 翻译功能报错？
A: 检查翻译服务配置，确认API密钥有效，或尝试其他翻译服务。

### Q: 扫描任务一直排队？
A: 检查扫描工具是否正确安装，查看错误日志获取详细信息。

更多问题请查看项目Issues或提交新的Issue。
