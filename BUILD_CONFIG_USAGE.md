# 编译配置热配置使用说明

## 功能概述

编译配置热配置功能允许您为不同的项目类型和编程语言配置自定义的编译命令，无需修改代码即可适应各种项目的编译需求。

## 主要特性

1. **热配置**: 无需重启服务即可修改编译命令
2. **多语言支持**: 支持Java、JavaScript、Python、C#、C++、Go等语言
3. **项目类型识别**: 自动识别Maven、Gradle、NPM等项目类型
4. **默认配置**: 每种语言可设置默认编译配置
5. **项目级配置**: 单个项目可指定特定的编译配置
6. **环境变量支持**: 支持$JDK_HOME等环境变量

## 使用方法

### 1. 管理编译配置

#### 通过Admin界面管理
访问: `http://localhost:7000/admin/core/buildconfig/`

- 查看所有编译配置
- 添加新配置
- 编辑现有配置
- 设置默认配置

#### 通过API管理
```bash
# 获取所有配置
GET /api/v1/build-configs/

# 按语言获取配置
GET /api/v1/build-configs/by_language/?language=java

# 获取默认配置
GET /api/v1/build-configs/defaults/

# 创建新配置
POST /api/v1/build-configs/
{
    "name": "Spring Boot项目",
    "language": "java",
    "project_type": "maven",
    "build_command": "env JAVA_HOME=$JDK_HOME PATH=$JDK_HOME/bin:$PATH mvn clean compile -DskipTests -Dmaven.test.skip=true",
    "description": "Spring Boot项目的编译配置",
    "is_default": false,
    "is_active": true
}

# 设置为默认配置
POST /api/v1/build-configs/{id}/set_default/

# 测试编译命令
POST /api/v1/build-configs/test_command/
{
    "command": "env JAVA_HOME=$JDK_HOME PATH=$JDK_HOME/bin:$PATH mvn clean compile",
    "test_path": "/tmp"
}
```

### 2. 配置项目编译

#### 方式一：项目级配置（优先级最高）
在项目设置中指定特定的编译配置：

```python
# 通过Admin界面或API设置
project.build_config = BuildConfig.objects.get(name="Spring Boot项目")
project.save()
```

#### 方式二：自动选择配置
系统会根据项目类型自动选择合适的配置：

- Java + pom.xml → Maven配置
- Java + build.gradle → Gradle配置  
- JavaScript + package.json → NPM配置

#### 方式三：默认配置
如果没有找到匹配的配置，使用该语言的默认配置。

### 3. 预置配置

系统已预置以下配置：

#### Java配置
```bash
# Maven标准配置（默认）
env JAVA_HOME=$JDK_HOME PATH=$JDK_HOME/bin:$PATH mvn clean compile -DskipTests

# Gradle标准配置
env JAVA_HOME=$JDK_HOME PATH=$JDK_HOME/bin:$PATH ./gradlew build -x test
```

#### JavaScript配置
```bash
# NPM标准配置（默认）
npm install --ignore-scripts --no-audit --no-fund --legacy-peer-deps

# Yarn配置
yarn install --ignore-scripts --ignore-engines
```

### 4. 环境变量

支持的环境变量：
- `$JDK_HOME`: JDK安装路径
- 其他自定义环境变量可在settings.py中配置

### 5. 初始化默认配置

```bash
# 运行管理命令初始化默认配置
python3 manage.py init_build_configs
```

## 配置示例

### Java Maven项目
```json
{
    "name": "Maven多模块项目",
    "language": "java",
    "project_type": "maven",
    "build_command": "env JAVA_HOME=$JDK_HOME PATH=$JDK_HOME/bin:$PATH mvn clean compile -DskipTests -T 4",
    "description": "Maven多模块项目，使用4线程编译",
    "is_default": false
}
```

### JavaScript React项目
```json
{
    "name": "React项目",
    "language": "javascript", 
    "project_type": "react",
    "build_command": "npm install --legacy-peer-deps && npm run build",
    "description": "React项目编译配置",
    "is_default": false
}
```

### Java Gradle项目
```json
{
    "name": "Gradle Android项目",
    "language": "java",
    "project_type": "gradle",
    "build_command": "env JAVA_HOME=$JDK_HOME PATH=$JDK_HOME/bin:$PATH ./gradlew assembleDebug -x test --parallel",
    "description": "Android项目编译配置",
    "is_default": false
}
```

## 工作流程

1. **扫描开始**: 系统检测项目语言和类型
2. **配置选择**: 按优先级选择编译配置
   - 项目指定配置 > 项目类型匹配配置 > 语言默认配置
3. **命令执行**: 替换环境变量并执行编译命令
4. **扫描继续**: 使用编译结果进行安全扫描

## 注意事项

1. **权限**: 确保编译命令有足够的执行权限
2. **路径**: 使用绝对路径或确保相对路径正确
3. **超时**: 复杂项目可能需要调整超时时间
4. **依赖**: 确保编译工具（Maven、Gradle、NPM等）已安装
5. **环境变量**: 确保$JDK_HOME等环境变量正确设置

## 故障排除

### 编译失败
1. 检查编译命令语法
2. 验证环境变量设置
3. 确认编译工具可用
4. 查看扫描日志获取详细错误信息

### 配置不生效
1. 确认配置已启用（is_active=True）
2. 检查项目类型匹配规则
3. 验证默认配置设置

### 性能问题
1. 使用并行编译选项（如Maven的-T参数）
2. 跳过不必要的测试（-DskipTests）
3. 调整超时时间设置

## API参考

完整的API文档请访问: `http://localhost:7000/api/docs/`

主要端点：
- `GET /api/v1/build-configs/` - 获取所有配置
- `POST /api/v1/build-configs/` - 创建配置
- `PUT /api/v1/build-configs/{id}/` - 更新配置
- `DELETE /api/v1/build-configs/{id}/` - 删除配置
- `POST /api/v1/build-configs/{id}/set_default/` - 设为默认
- `POST /api/v1/build-configs/test_command/` - 测试命令