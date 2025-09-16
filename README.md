# 智能代码安全分析平台 (开源版)

基于Django和DefectDojo架构设计的现代化代码安全漏洞管理平台，集成AI分析能力和自动扫描功能。

## 🚀 功能特性

- **自动扫描**: 支持CodeQL、Semgrep等多种扫描工具
- **智能队列**: 扫描任务自动排队，避免资源冲突  
- **报告解析**: 自动解析SARIF格式报告
- **漏洞管理**: 完整的漏洞生命周期管理
- **统计分析**: 丰富的安全统计和报告功能
- **AI增强**: 提供AI分析框架，用户可自行改造 `ai_analysis/services.py` 脚本接入所需AI服务 (可选)
- **动态刷新**: 自动检测并加载新的报告文件

## 🛠️ 快速开始

### 仅用于报告展示

如果您只需要展示已有的扫描报告，无需进行实际扫描：

1. **放置文件**: 将SARIF报告放到 `workspace/reports/`，源代码放到 `workspace/projects/`
2. **一键安装**: `./install.sh`
3. **启动平台**: `./platform.sh start`
4. **访问平台**: http://localhost:7000

### 完整安装使用

```bash
# 1. 克隆项目
git clone https://github.com/jhonxie369-star/smart_security_analyzer_opensource.git
cd smart_security_analyzer_opensource

# 2. 一键安装
./install.sh

# 3. 启动平台
./platform.sh start

# 4. 访问平台
# 浏览器打开: http://localhost:7000
```

## 📋 平台管理

使用 `platform.sh` 脚本管理平台：

```bash
# 平台控制
./platform.sh start      # 启动平台
./platform.sh stop       # 停止平台  
./platform.sh restart    # 重启平台
./platform.sh status     # 查看状态
./platform.sh logs       # 查看日志

# 数据管理
./platform.sh init       # 初始化数据
./platform.sh import     # 导入报告
./platform.sh clean      # 清理数据
```

## 🔧 扫描工具配置 (可选)

如需进行实际扫描，请安装相应工具：

### CodeQL
```bash
# 下载到 tools/codeql/ 目录
# https://github.com/github/codeql-cli-binaries/releases
```

### Semgrep  
```bash
pip install semgrep
```

## 📁 目录结构

```
smart_security_analyzer/
├── workspace/           # 工作空间
│   ├── reports/        # 扫描报告 (SARIF格式)
│   └── projects/       # 项目源码
├── tools/              # 扫描工具 (需自行安装)
├── *.sh               # 管理脚本
└── README.md          # 说明文档
```

## 🌟 特色功能

- **零配置启动**: 一键安装和启动
- **自动发现**: 动态检测workspace中的新报告
- **智能解析**: 自动解析多种格式的安全报告
- **可视化展示**: 丰富的图表和统计信息
- **AI辅助**: 可选的AI分析和翻译功能

## 📝 更多文档

- [开发指南](DEVELOPMENT_GUIDE.md)
- [构建配置](BUILD_CONFIG_USAGE.md)
- [项目开发](PROJECT_DEVELOPMENT_GUIDE.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

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

## 🔧 自定义配置 (可选)

### AI分析功能
如需使用AI分析功能，请自行修改 `ai_analysis/services.py` 脚本接入所需的AI服务。

### 翻译功能  
如需使用翻译功能，请自行修改 `translation/services.py` 脚本接入所需的翻译服务。

## 📚 更多文档

- [开发指南](DEVELOPMENT_GUIDE.md)
- [构建配置](BUILD_CONFIG_USAGE.md)
- [项目开发](PROJECT_DEVELOPMENT_GUIDE.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## ⭐ 特别说明

本项目为开源版本，部分高级功能需要自行配置相应的服务和API密钥。
