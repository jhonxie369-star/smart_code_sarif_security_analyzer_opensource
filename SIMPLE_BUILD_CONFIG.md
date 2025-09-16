# 简单编译命令配置

## 功能说明

为项目添加了简单的编译命令配置功能，支持自定义编译命令，不设置则使用默认命令。

## 使用方法

### 1. 快速扫描页面配置

访问: `http://localhost:7000/api/quick-scan/`

在"编译命令"输入框中填写自定义编译命令，留空则使用默认命令。

**默认命令:**
- Java: `env JAVA_HOME=$JDK_HOME PATH=$JDK_HOME/bin:$PATH mvn clean compile -DskipTests`
- JavaScript: `npm install --ignore-scripts --no-audit --no-fund --legacy-peer-deps`

**自定义示例:**
```bash
# Java项目跳过更多检查
mvn clean compile -DskipTests -Dmaven.test.skip=true -Dcheckstyle.skip=true

# JavaScript项目使用yarn
yarn install --ignore-scripts --ignore-engines

# Gradle项目
./gradlew build -x test --parallel
```

### 2. 项目管理界面配置

访问: `http://localhost:7000/admin/core/project/`

在项目编辑页面的"编译命令"字段中设置自定义命令。

### 3. 工作原理

1. **扫描开始**: 系统检测项目语言
2. **命令选择**: 
   - 如果项目设置了`build_command`，使用自定义命令
   - 否则使用对应语言的默认命令
3. **命令执行**: 在项目根目录执行编译命令
4. **继续扫描**: 使用编译结果进行安全扫描

### 4. 环境变量支持

- `$JDK_HOME`: 自动替换为JDK路径
- 其他环境变量可直接使用

### 5. 常见配置示例

#### Java Maven项目
```bash
# 标准配置
mvn clean compile -DskipTests

# 多线程编译
mvn clean compile -DskipTests -T 4

# 跳过所有检查
mvn clean compile -DskipTests -Dmaven.test.skip=true -Dcheckstyle.skip=true -Dpmd.skip=true
```

#### Java Gradle项目
```bash
# 标准配置
./gradlew build -x test

# 并行编译
./gradlew build -x test --parallel

# Android项目
./gradlew assembleDebug -x test
```

#### JavaScript项目
```bash
# NPM标准
npm install --ignore-scripts --no-audit --no-fund

# Yarn
yarn install --ignore-scripts --ignore-engines

# 包含构建步骤
npm install && npm run build
```

## 数据库字段

项目模型新增字段:
- `build_command`: 文本字段，存储自定义编译命令，可为空

## 注意事项

1. **路径**: 命令在项目根目录执行
2. **权限**: 确保命令有执行权限
3. **超时**: 复杂项目注意超时设置
4. **依赖**: 确保编译工具已安装

这个简化版本满足您的需求：不设置就用默认，设置了就用自定义的，简单直接。