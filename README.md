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

**默认登录信息:**
- 用户名: `admin`
- 密码: `admin123`

### 完整安装使用

```bash
# 1. 克隆项目
git clone https://github.com/jhonxie369-star/smart_security_analyzer_opensource.git
cd smart_security_analyzer_opensource

# 2. 一键安装
./install.sh

# 3. 启动平台
./platform.sh start

# 4. 访问平台 (默认用户名: admin, 密码: admin123)
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
- **AI辅助**: 可选的AI分析功能，默认支持翻译功能

## 📝 更多文档

- [项目开发指南](PROJECT_DEVELOPMENT_GUIDE.md)
- [构建配置说明](BUILD_CONFIG_USAGE.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🎯 使用指南

### 快速扫描
访问 `http://localhost:7000/api/quick-scan/` 进行快速扫描

### 管理界面  
访问 `http://localhost:7000/admin/` 进行系统管理

## 🎯 数据管理

### 默认管理员账户
安装完成后，系统会自动创建默认管理员账户：
- **用户名**: `admin`
- **密码**: `admin123`
- **登录地址**: http://localhost:7000/admin/

⚠️ **安全提醒**: 生产环境请立即修改默认密码！

### 数据管理命令

#### 1. 初始化数据 - `./platform.sh init`
**功能**: 增量初始化部门和项目
- 扫描 `workspace/reports/` 目录结构
- 根据目录结构自动创建部门和项目
- 只添加数据库中不存在的新项目
- 不会删除已有数据

**使用场景**:
- 首次部署后初始化项目结构
- 添加新项目到系统中
- 恢复意外删除的项目记录

#### 2. 导入报告 - `./platform.sh import`
**功能**: 增量导入SARIF报告文件
- 扫描 `workspace/reports/` 下的所有 `.sarif` 文件
- 智能检测已导入的报告，避免重复导入
- 将新漏洞数据导入到对应项目中
- 自动创建扫描任务记录

**使用场景**:
- 导入新的扫描报告
- 日常增量更新漏洞数据
- 批量导入新报告而不影响已有数据

**相关命令**:
```bash
./platform.sh import          # 增量导入（推荐）
./platform.sh import-force    # 强制重新导入所有报告
./platform.sh import-preview  # 预览将要导入的报告
```

#### 3. 清理数据 - `./platform.sh clean`
**功能**: 清理数据库中不存在的项目
- 检查数据库中的项目是否在文件系统中存在
- 删除文件系统中已不存在的项目记录
- 同时清理相关的扫描任务和漏洞数据

**使用场景**:
- 清理已删除项目的数据库记录
- 保持数据库与文件系统同步
- 释放数据库存储空间

**⚠️ 警告**: 此操作会永久删除数据，请谨慎使用！

### 目录结构要求

为确保源代码定位功能正常工作，**项目目录结构必须与报告目录结构保持一致**：

```
workspace/
├── reports/                    # 报告目录
│   └── 部门名/
│       └── 项目名/
│           └── 扫描报告.sarif
└── projects/                   # 源代码目录
    └── 部门名/
        └── 项目名/
            ├── src/
            ├── pom.xml
            └── ...源代码文件
```

**示例**:
```
workspace/
├── reports/
│   └── cyber/
│       └── balance-server/
│           └── balance-server_codeql_report_20250708.sarif
└── projects/
    └── cyber/
        └── balance-server/
            ├── src/main/java/
            ├── pom.xml
            └── README.md
```

## 🎯 功能使用

### 快速扫描

## 🔧 AI功能配置 (可选)

## 🔧 自定义配置 (可选)

### AI分析功能
如需使用AI分析功能，请自行修改 `ai_analysis/services.py` 脚本接入所需的AI服务。

### 翻译功能  
平台默认支持翻译功能，如需自定义翻译服务，可修改 `translation/services.py` 脚本。

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
