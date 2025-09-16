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

## 🛠️ 快速开始

### 仅用于报告展示

如果您只需要展示已有的扫描报告，无需进行实际扫描，可以：

1. **放置报告文件**: 将SARIF格式的扫描报告放到 `workspace/reports/` 目录下
2. **放置源代码**: 将对应的源代码文件放到 `workspace/projects/` 目录下
3. **启动平台**: 按照下面的步骤启动平台即可完成报告展示

目录结构示例：
```
workspace/
├── reports/
│   └── your-project/
│       └── scan-report.sarif
└── projects/
    └── your-project/
        └── src/
```

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd smart_security_analyzer

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装基础依赖
pip install -r requirements.txt
```

### 2. 扫描工具安装

#### CodeQL 安装
```bash
# 下载 CodeQL CLI 到 tools/codeql/ 目录
# 访问: https://github.com/github/codeql-cli-binaries/releases

# 下载 CodeQL 查询规则到 tools/codeql-rules/ 目录  
# 访问: https://github.com/github/codeql
```

#### Semgrep 安装
```bash
pip install semgrep
```

#### JDK 安装 (Java项目需要)
```bash
# 创建软链接到系统JDK
ln -s /usr/lib/jvm/java-11-openjdk-amd64 tools/jdk
```

### 3. 数据库配置

```bash
# 安装 PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# 创建数据库
sudo -u postgres createdb smart_security_analyzer

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件中的数据库配置
```

### 4. 初始化应用

```bash
# 运行数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动服务
python manage.py runserver 0.0.0.0:7000
```

## 🎯 使用指南

### 快速扫描
访问 `http://localhost:7000/api/quick-scan/` 进行快速扫描

### 管理界面  
访问 `http://localhost:7000/admin/` 进行系统管理

### 任务监控
访问 `http://localhost:7000/api/task-monitor/` 查看扫描任务

## 🔧 AI功能配置 (可选)

### AI分析功能

支持多种AI服务：

#### OpenAI 配置
```bash
pip install openai

# 在 .env 中配置
AI_PROVIDER=openai
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-3.5-turbo
```

#### Azure OpenAI 配置
```bash
pip install openai

# 在 .env 中配置
AI_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-key
```

### 翻译功能

#### Google翻译 (免费)
```bash
pip install googletrans==4.0.0rc1

# 在 .env 中配置
TRANSLATION_PROVIDER=google
```

#### 本地翻译模型
```bash
pip install transformers torch

# 在 .env 中配置  
TRANSLATION_PROVIDER=local
```

## 📚 详细文档

- [完整安装指南](README_OPENSOURCE.md)
- [开发指南](DEVELOPMENT_GUIDE.md)
- [项目开发指南](PROJECT_DEVELOPMENT_GUIDE.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## ⭐ 特别说明

本项目为开源版本，部分高级功能需要自行配置相应的服务和API密钥。
