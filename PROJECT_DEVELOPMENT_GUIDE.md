# 智能代码安全分析平台 - 完整开发指南

## 📋 项目概述

### 项目定位
基于Django和DefectDojo架构设计的现代化代码安全漏洞管理平台，集成AI分析能力和自动扫描功能。

### 核心价值
- **自动化扫描**：支持CodeQL、Semgrep等主流工具
- **智能分析**：AI驱动的漏洞分析和翻译
- **企业级管理**：部门/项目层级管理
- **实时监控**：扫描队列和日志监控

## 🏗️ 技术架构

### 技术栈选择
```
后端框架: Django 4.2 + Django REST Framework
数据库: PostgreSQL 
缓存: Django Database Cache
AI服务: OpenAI API
扫描工具: CodeQL, Semgrep
部署: Gunicorn + WhiteNoise
```

### 架构设计原则
1. **模块化设计**：核心功能独立模块
2. **相对路径**：便于迁移部署
3. **队列机制**：避免扫描冲突
4. **三级分级**：简化漏洞严重程度

## 📁 项目结构设计

```
smart_security_analyzer/
├── smart_security_analyzer/          # Django项目配置
│   ├── settings.py                   # 核心配置文件
│   ├── urls.py                       # 主路由配置
│   ├── wsgi.py                       # WSGI配置
│   └── celery.py                     # Celery配置(可选)
├── core/                             # 核心业务模块
│   ├── models.py                     # 数据模型定义
│   ├── admin.py                      # 管理后台配置
│   ├── views.py                      # 视图逻辑
│   ├── urls.py                       # 路由配置
│   ├── scanner.py                    # 扫描引擎
│   ├── scan_queue.py                 # 扫描队列管理
│   ├── git_utils.py                  # Git操作工具
│   ├── cwe_utils.py                  # CWE工具类
│   ├── middleware.py                 # 中间件
│   ├── scanners/                     # 扫描器实现
│   │   ├── base.py                   # 基础扫描器
│   │   ├── codeql.py                 # CodeQL扫描器
│   │   └── semgrep.py                # Semgrep扫描器
│   └── management/commands/          # Django命令
├── api/                              # REST API模块
│   ├── views.py                      # API视图
│   ├── serializers.py                # 序列化器
│   ├── urls.py                       # API路由
│   └── documentation_views.py        # API文档视图
├── parsers/                          # 报告解析模块
│   ├── sarif_parser.py               # SARIF解析器
│   └── vulnerability_scoring.py      # 漏洞评分
├── ai_analysis/                      # AI分析模块
│   └── services.py                   # AI分析服务
├── translation/                      # 翻译模块
│   └── services.py                   # 翻译服务
├── statistics/                       # 统计模块
│   └── services.py                   # 统计服务
├── templates/                        # 模板文件
│   ├── admin/                        # 管理后台模板
│   ├── api/                          # API文档模板
│   └── scan/                         # 扫描相关模板
├── static/                           # 静态文件
│   ├── css/                          # 样式文件
│   └── js/                           # JavaScript文件
├── workspace/                        # 工作空间
│   ├── projects/                     # 项目源码存储
│   ├── reports/                      # 扫描报告
│   └── scan_temp/                    # 临时扫描目录
├── tools/                            # 扫描工具
│   ├── codeql/                       # CodeQL工具
│   ├── codeql-rules/                 # CodeQL规则
│   └── jdk/                          # JDK工具
├── logs/                             # 日志文件
├── requirements.txt                  # Python依赖
├── manage.py                         # Django管理脚本
└── .env                              # 环境配置
```

## 🗄️ 数据模型设计

### 1. 核心模型关系
```
Department (部门)
    ↓ 1:N
Project (项目)
    ↓ 1:N
ScanTask (扫描任务)
    ↓ 1:N
Finding (漏洞发现)
    ↓ 1:N
FindingNote (漏洞备注)
StatusHistory (状态历史)
```

### 2. 模型字段设计

#### Department 模型
```python
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    lead = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### Project 模型
```python
class Project(models.Model):
    name = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    code_owner = models.CharField(max_length=100)
    tech_lead = models.CharField(max_length=100, blank=True)
    git_url = models.CharField(max_length=500, blank=True)
    git_branch = models.CharField(max_length=100, default='master')
    auto_scan_enabled = models.BooleanField(default=False)
    business_criticality = models.CharField(max_length=20, choices=[...])
    build_command = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### ScanTask 模型
```python
class ScanTask(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    tool_name = models.CharField(max_length=50, choices=TOOL_CHOICES)
    scan_type = models.CharField(max_length=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    report_file = models.CharField(max_length=1000, blank=True)
    scan_config = models.JSONField(default=dict)
    total_findings = models.IntegerField(default=0)
    # 三级分级统计
    critical_count = models.IntegerField(default=0)  # 高危
    high_count = models.IntegerField(default=0)      # 中危
    medium_count = models.IntegerField(default=0)    # 低危
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    scan_log = models.TextField(blank=True)
```

#### Finding 模型 (核心)
```python
class Finding(models.Model):
    # 基础信息
    title = models.CharField(max_length=511)
    date = models.DateField(default=timezone.now)
    
    # 严重程度 - 三级分级
    severity = models.CharField(max_length=200, choices=[
        ("低危", "低危"), ("中危", "中危"), ("高危", "高危")
    ])
    numerical_severity = models.CharField(max_length=4, blank=True)
    
    # CVSS评分
    cvssv3 = models.TextField(max_length=117, null=True, blank=True)
    cvssv3_score = models.FloatField(null=True, blank=True)
    
    # CWE分类
    cwe = models.IntegerField(default=0, null=True, blank=True)
    
    # 描述信息
    description = models.TextField(blank=True)
    message = models.TextField(blank=True)
    translated_message = models.TextField(blank=True)
    
    # 位置信息
    file_path = models.CharField(max_length=1000, blank=True)
    line_number = models.IntegerField(null=True, blank=True)
    column_number = models.IntegerField(null=True, blank=True)
    
    # 状态管理 (借鉴DefectDojo)
    active = models.BooleanField(default=True)
    verified = models.BooleanField(default=False)
    false_p = models.BooleanField(default=False)
    duplicate = models.BooleanField(default=False)
    out_of_scope = models.BooleanField(default=False)
    risk_accepted = models.BooleanField(default=False)
    under_review = models.BooleanField(default=False)
    is_mitigated = models.BooleanField(default=False)
    
    # AI分析
    ai_analysis = models.JSONField(default=dict)
    ai_cached = models.BooleanField(default=False)
    ai_analyzing = models.BooleanField(default=False)
    
    # 关联关系
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    scan_task = models.ForeignKey(ScanTask, on_delete=models.CASCADE)
```

## ⚙️ 核心配置文件

### settings.py 关键配置
```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# 环境变量加载
def load_env_file(env_path):
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_env_file(BASE_DIR / '.env')

# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'smart_security_analyzer'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# 自动扫描配置
AUTO_SCAN_CONFIG = {
    'ENABLED': os.getenv('AUTO_SCAN_ENABLED', 'True').lower() == 'true',
    'WORK_DIR': os.getenv('SCAN_WORK_DIR', str(BASE_DIR / 'workspace' / 'scan_temp')),
    'OUTPUT_DIR': os.getenv('SCAN_OUTPUT_DIR', str(BASE_DIR / 'workspace' / 'reports')),
    'PROJECT_DIR': os.getenv('SCAN_PROJECT_DIR', str(BASE_DIR / 'workspace' / 'projects')),
    'TIMEOUT': int(os.getenv('SCAN_TIMEOUT', '3600')),
    'TOOLS': {
        'CODEQL_RULES': os.getenv('CODEQL_RULES', str(BASE_DIR / 'tools' / 'codeql-rules')),
        'CODEQL_BIN': os.getenv('CODEQL_BIN', str(BASE_DIR / 'tools' / 'codeql' / 'codeql')),
        'SEMGREP_BIN': os.getenv('SEMGREP_BIN', 'semgrep'),
        'JDK_HOME': os.getenv('JDK_HOME', str(BASE_DIR / 'tools' / 'jdk')),
    }
}

# AI配置
AI_CONFIG = {
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
    'OPENAI_MODEL': os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
    'CACHE_ENABLED': True,
    'TIMEOUT': 90,
}

# 登录配置
DISABLE_LOGIN = os.getenv('DISABLE_LOGIN', 'False').lower() == 'true'
AUTO_LOGIN_USER = os.getenv('AUTO_LOGIN_USER', 'admin')
```

## 🔧 核心功能实现

### 1. 扫描队列系统

#### scan_queue.py
```python
import threading
import queue
import logging
from datetime import datetime

class ScanQueue:
    def __init__(self):
        self.task_queue = queue.Queue()
        self.running_tasks = {}
        self.completed_tasks = {}
        self.worker_thread = None
        self.is_running = False
        self.lock = threading.Lock()
    
    def start_worker(self):
        """启动工作线程"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
    
    def _worker(self):
        """工作线程主循环"""
        while self.is_running:
            try:
                task_id, task_func = self.task_queue.get(timeout=1)
                
                with self.lock:
                    self.running_tasks[task_id] = {
                        'start_time': datetime.now(),
                        'status': 'running'
                    }
                
                try:
                    result = task_func()
                    status = 'completed'
                except Exception as e:
                    result = str(e)
                    status = 'failed'
                
                with self.lock:
                    self.completed_tasks[task_id] = {
                        'result': result,
                        'status': status,
                        'end_time': datetime.now()
                    }
                    del self.running_tasks[task_id]
                
                self.task_queue.task_done()
                
            except queue.Empty:
                continue
    
    def add_task(self, task_id, task_func):
        """添加任务到队列"""
        self.task_queue.put((task_id, task_func))
        if not self.is_running:
            self.start_worker()
    
    def get_queue_status(self):
        """获取队列状态"""
        with self.lock:
            return {
                'queue_size': self.task_queue.qsize(),
                'running_tasks': len(self.running_tasks),
                'completed_tasks': len(self.completed_tasks),
                'running_task_ids': list(self.running_tasks.keys())
            }

# 全局队列实例
scan_queue = ScanQueue()
```

### 2. 自动扫描引擎

#### scanner.py
```python
import os
import subprocess
import tempfile
from datetime import datetime
from django.conf import settings

class AutoScanner:
    def __init__(self, project):
        self.project = project
        self.work_dir = settings.AUTO_SCAN_CONFIG['WORK_DIR']
        self.output_dir = settings.AUTO_SCAN_CONFIG['OUTPUT_DIR']
        self.project_dir = settings.AUTO_SCAN_CONFIG['PROJECT_DIR']
    
    def execute_scan(self, git_url, branch, scan_task):
        """执行完整扫描流程"""
        try:
            scan_task.status = 'running'
            scan_task.started_at = datetime.now()
            scan_task.save()
            
            # 1. 克隆代码
            project_path = self._clone_repository(git_url, branch, scan_task)
            
            # 2. 检测语言
            languages = self._detect_languages(project_path, scan_task)
            
            # 3. 执行扫描
            report_files = []
            for lang in languages:
                if lang in ['javascript', 'typescript']:
                    report_file = self._run_codeql_scan(project_path, 'javascript', scan_task)
                elif lang == 'java':
                    report_file = self._run_codeql_scan(project_path, 'java', scan_task)
                elif lang == 'python':
                    report_file = self._run_semgrep_scan(project_path, scan_task)
                
                if report_file:
                    report_files.append(report_file)
            
            # 4. 解析报告
            total_findings = 0
            for report_file in report_files:
                findings = self._parse_sarif_report(report_file, scan_task)
                total_findings += len(findings)
            
            # 5. 更新任务状态
            scan_task.status = 'completed'
            scan_task.completed_at = datetime.now()
            scan_task.total_findings = total_findings
            scan_task.save()
            
            return True
            
        except Exception as e:
            scan_task.status = 'failed'
            scan_task.error_message = str(e)
            scan_task.save()
            raise
    
    def _clone_repository(self, git_url, branch, scan_task):
        """克隆Git仓库"""
        project_path = os.path.join(
            self.project_dir, 
            self.project.department.name, 
            self.project.name
        )
        
        # 清理旧目录
        if os.path.exists(project_path):
            subprocess.run(f"rm -rf '{project_path}'", shell=True)
        
        os.makedirs(project_path, exist_ok=True)
        
        # 克隆代码
        cmd = f"git clone --depth 1 --branch {branch} {git_url} {project_path}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Git克隆失败: {result.stderr}")
        
        self._log_scan_progress(scan_task, f"代码克隆完成: {project_path}")
        return project_path
    
    def _detect_languages(self, project_path, scan_task):
        """检测项目语言"""
        languages = []
        
        # JavaScript/TypeScript检测
        if (os.path.exists(os.path.join(project_path, 'package.json')) or
            any(f.endswith(('.js', '.ts', '.jsx', '.tsx')) 
                for f in os.listdir(project_path) if os.path.isfile(os.path.join(project_path, f)))):
            languages.append('javascript')
        
        # Java检测
        if (os.path.exists(os.path.join(project_path, 'pom.xml')) or
            os.path.exists(os.path.join(project_path, 'build.gradle')) or
            any(f.endswith('.java') 
                for f in os.listdir(project_path) if os.path.isfile(os.path.join(project_path, f)))):
            languages.append('java')
        
        # Python检测
        if (os.path.exists(os.path.join(project_path, 'requirements.txt')) or
            os.path.exists(os.path.join(project_path, 'setup.py')) or
            any(f.endswith('.py') 
                for f in os.listdir(project_path) if os.path.isfile(os.path.join(project_path, f)))):
            languages.append('python')
        
        self._log_scan_progress(scan_task, f"检测到语言: {', '.join(languages)}")
        return languages
    
    def _run_codeql_scan(self, project_path, language, scan_task):
        """执行CodeQL扫描"""
        codeql_bin = settings.AUTO_SCAN_CONFIG['TOOLS']['CODEQL_BIN']
        codeql_rules = settings.AUTO_SCAN_CONFIG['TOOLS']['CODEQL_RULES']
        
        # 创建数据库
        db_path = os.path.join(self.work_dir, f"codeql-db-{self.project.id}")
        
        self._log_scan_progress(scan_task, f"开始CodeQL {language}扫描...")
        
        # 创建数据库命令
        create_cmd = f"{codeql_bin} database create {db_path} --language={language} --source-root={project_path}"
        
        if language == 'java':
            create_cmd += f" --command='mvn clean compile -DskipTests'"
        elif language == 'javascript':
            create_cmd += f" --command='npm install || yarn install || true'"
        
        result = subprocess.run(create_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"CodeQL数据库创建失败: {result.stderr}")
        
        # 分析数据库
        report_file = os.path.join(
            self.output_dir,
            self.project.department.name,
            self.project.name,
            f"codeql_{language}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sarif"
        )
        
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        analyze_cmd = f"{codeql_bin} database analyze {db_path} {codeql_rules}/{language}/ql/src/codeql-suites/{language}-security-and-quality.qls --format=sarif-latest --output={report_file}"
        
        result = subprocess.run(analyze_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"CodeQL分析失败: {result.stderr}")
        
        # 清理数据库
        subprocess.run(f"rm -rf {db_path}", shell=True)
        
        self._log_scan_progress(scan_task, f"CodeQL {language}扫描完成: {report_file}")
        return report_file
    
    def _run_semgrep_scan(self, project_path, scan_task):
        """执行Semgrep扫描"""
        self._log_scan_progress(scan_task, "开始Semgrep扫描...")
        
        report_file = os.path.join(
            self.output_dir,
            self.project.department.name,
            self.project.name,
            f"semgrep_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sarif"
        )
        
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        cmd = f"semgrep --config=auto --sarif --output={report_file} {project_path}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode not in [0, 1]:  # Semgrep返回1表示发现问题，这是正常的
            raise Exception(f"Semgrep扫描失败: {result.stderr}")
        
        self._log_scan_progress(scan_task, f"Semgrep扫描完成: {report_file}")
        return report_file
    
    def _parse_sarif_report(self, report_file, scan_task):
        """解析SARIF报告"""
        from parsers.sarif_parser import parse_sarif_file
        
        findings = parse_sarif_file(report_file, self.project, scan_task)
        
        # 批量创建漏洞记录
        from core.models import Finding
        Finding.objects.bulk_create(findings)
        
        self._log_scan_progress(scan_task, f"报告解析完成，发现 {len(findings)} 个漏洞")
        return findings
    
    def _log_scan_progress(self, scan_task, message):
        """记录扫描进度"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"{timestamp} {message}\n"
        
        if scan_task.scan_log:
            scan_task.scan_log += log_entry
        else:
            scan_task.scan_log = log_entry
        
        scan_task.save()
```

### 3. SARIF报告解析器

#### parsers/sarif_parser.py
```python
import json
import os
from core.models import Finding, SeverityManager

def parse_sarif_file(file_path, project, scan_task):
    """解析SARIF格式的扫描报告"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"报告文件不存在: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        sarif_data = json.load(f)
    
    findings = []
    
    for run in sarif_data.get('runs', []):
        tool_name = run.get('tool', {}).get('driver', {}).get('name', 'unknown')
        rules = {rule['id']: rule for rule in run.get('tool', {}).get('driver', {}).get('rules', [])}
        
        for result in run.get('results', []):
            finding = _parse_sarif_result(result, rules, project, scan_task, tool_name)
            if finding:
                findings.append(finding)
    
    return findings

def _parse_sarif_result(result, rules, project, scan_task, tool_name):
    """解析单个SARIF结果"""
    rule_id = result.get('ruleId', 'unknown')
    rule = rules.get(rule_id, {})
    
    # 基础信息
    title = result.get('message', {}).get('text', rule.get('shortDescription', {}).get('text', rule_id))
    description = rule.get('fullDescription', {}).get('text', '')
    
    # 严重程度转换 - 三级分级
    level = result.get('level', 'warning')
    severity = SeverityManager.sarif_level_to_severity(level)
    
    # 位置信息
    locations = result.get('locations', [])
    file_path = ''
    line_number = None
    column_number = None
    
    if locations:
        location = locations[0]
        physical_location = location.get('physicalLocation', {})
        artifact_location = physical_location.get('artifactLocation', {})
        file_path = artifact_location.get('uri', '')
        
        region = physical_location.get('region', {})
        line_number = region.get('startLine')
        column_number = region.get('startColumn')
    
    # CWE提取
    cwe = _extract_cwe_from_rule(rule)
    
    # 创建Finding对象
    finding = Finding(
        title=title[:511],  # 限制长度
        description=description,
        message=result.get('message', {}).get('text', ''),
        severity=severity,
        file_path=file_path,
        line_number=line_number,
        column_number=column_number,
        cwe=cwe,
        project=project,
        scan_task=scan_task,
        vuln_id_from_tool=rule_id,
        unique_id_from_tool=f"{tool_name}_{rule_id}_{file_path}_{line_number}"
    )
    
    return finding

def _extract_cwe_from_rule(rule):
    """从规则中提取CWE编号"""
    # 检查properties中的CWE信息
    properties = rule.get('properties', {})
    
    # 常见的CWE字段
    cwe_fields = ['cwe', 'CWE', 'security-severity']
    for field in cwe_fields:
        if field in properties:
            cwe_value = properties[field]
            if isinstance(cwe_value, str) and 'CWE-' in cwe_value:
                try:
                    return int(cwe_value.split('CWE-')[1].split('/')[0])
                except:
                    pass
    
    # 检查tags中的CWE信息
    tags = properties.get('tags', [])
    for tag in tags:
        if isinstance(tag, str) and tag.startswith('CWE-'):
            try:
                return int(tag.split('CWE-')[1])
            except:
                pass
    
    return None
```

### 4. AI分析服务

#### ai_analysis/services.py
```python
import openai
import json
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class AIAnalysisService:
    def __init__(self):
        self.api_key = settings.AI_CONFIG.get('OPENAI_API_KEY')
        self.model = settings.AI_CONFIG.get('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.timeout = settings.AI_CONFIG.get('TIMEOUT', 90)
        
        if self.api_key:
            openai.api_key = self.api_key
    
    def analyze_finding(self, finding):
        """分析单个漏洞"""
        if not self.api_key:
            return {'error': 'OpenAI API密钥未配置'}
        
        # 检查缓存
        cache_key = f"ai_analysis_{finding.id}_{finding.updated_at.timestamp()}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return {'analysis': cached_result, 'cached': True}
        
        try:
            # 构建分析提示
            prompt = self._build_analysis_prompt(finding)
            
            # 调用OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个代码安全专家，专门分析代码漏洞。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3,
                timeout=self.timeout
            )
            
            analysis_text = response.choices[0].message.content
            
            # 解析分析结果
            analysis_result = self._parse_analysis_result(analysis_text, finding)
            
            # 缓存结果
            cache.set(cache_key, analysis_result, timeout=86400)  # 缓存24小时
            
            return {'analysis': analysis_result, 'cached': False}
            
        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return {'error': f'AI分析失败: {str(e)}'}
    
    def batch_analyze_findings(self, findings, rule_id):
        """批量分析漏洞"""
        if not findings:
            return {'error': '没有提供漏洞数据'}
        
        # 检查是否已有缓存的分析结果
        cache_key = f"batch_ai_analysis_{rule_id}_{len(findings)}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return {'analysis': cached_result, 'cached': True}
        
        try:
            # 构建批量分析提示
            prompt = self._build_batch_analysis_prompt(findings, rule_id)
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个代码安全专家，专门批量分析同类型的代码漏洞。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3,
                timeout=self.timeout
            )
            
            analysis_text = response.choices[0].message.content
            analysis_result = self._parse_batch_analysis_result(analysis_text, rule_id)
            
            # 缓存结果
            cache.set(cache_key, analysis_result, timeout=86400)
            
            return {'analysis': analysis_result, 'cached': False}
            
        except Exception as e:
            logger.error(f"批量AI分析失败: {e}")
            return {'error': f'批量AI分析失败: {str(e)}'}
    
    def _build_analysis_prompt(self, finding):
        """构建单个漏洞分析提示"""
        return f"""
请分析以下代码安全漏洞：

漏洞标题: {finding.title}
漏洞描述: {finding.description or finding.message}
文件路径: {finding.file_path}
行号: {finding.line_number or '未知'}
CWE编号: {finding.cwe or '未知'}
严重程度: {finding.severity}

请提供以下分析：
1. 漏洞原理和成因
2. 潜在的安全风险
3. 修复建议和最佳实践
4. 是否为误报的判断

请用中文回答，格式为JSON：
{{
    "principle": "漏洞原理",
    "risk": "安全风险",
    "fix_suggestion": "修复建议", 
    "false_positive_likelihood": "误报可能性(低/中/高)",
    "severity_assessment": "严重程度评估"
}}
"""
    
    def _build_batch_analysis_prompt(self, findings, rule_id):
        """构建批量分析提示"""
        finding_list = []
        for i, finding in enumerate(findings[:5]):  # 限制最多5个样本
            finding_list.append(f"{i+1}. {finding.file_path}:{finding.line_number or '?'} - {finding.title}")
        
        return f"""
请分析以下同类型的代码安全漏洞（规则ID: {rule_id}）：

漏洞样本：
{chr(10).join(finding_list)}

总计 {len(findings)} 个相同类型的漏洞。

请提供统一的分析：
1. 这类漏洞的通用原理和成因
2. 整体安全风险评估
3. 通用的修复策略
4. 批量处理建议

请用中文回答，格式为JSON：
{{
    "rule_analysis": "规则分析",
    "common_cause": "通用成因",
    "risk_level": "风险等级",
    "fix_strategy": "修复策略",
    "batch_recommendation": "批量处理建议"
}}
"""
    
    def _parse_analysis_result(self, analysis_text, finding):
        """解析AI分析结果"""
        try:
            # 尝试解析JSON
            if '{' in analysis_text and '}' in analysis_text:
                json_start = analysis_text.find('{')
                json_end = analysis_text.rfind('}') + 1
                json_text = analysis_text[json_start:json_end]
                result = json.loads(json_text)
            else:
                # 如果不是JSON格式，创建基本结构
                result = {
                    "principle": "AI分析结果",
                    "risk": analysis_text[:200],
                    "fix_suggestion": "请参考完整分析内容",
                    "false_positive_likelihood": "中",
                    "severity_assessment": finding.severity
                }
            
            result['success'] = True
            result['raw_response'] = analysis_text
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'raw_response': analysis_text
            }
    
    def _parse_batch_analysis_result(self, analysis_text, rule_id):
        """解析批量分析结果"""
        try:
            if '{' in analysis_text and '}' in analysis_text:
                json_start = analysis_text.find('{')
                json_end = analysis_text.rfind('}') + 1
                json_text = analysis_text[json_start:json_end]
                result = json.loads(json_text)
            else:
                result = {
                    "rule_analysis": f"规则 {rule_id} 的分析",
                    "common_cause": analysis_text[:200],
                    "risk_level": "中等",
                    "fix_strategy": "请参考完整分析内容",
                    "batch_recommendation": "建议逐个审查"
                }
            
            result['success'] = True
            result['rule_id'] = rule_id
            result['raw_response'] = analysis_text
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'rule_id': rule_id,
                'raw_response': analysis_text
            }

# 全局服务实例
ai_analysis_service = AIAnalysisService()
```

### 5. REST API设计

#### api/serializers.py
```python
from rest_framework import serializers
from core.models import Department, Project, ScanTask, Finding

class DepartmentSerializer(serializers.ModelSerializer):
    project_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = '__all__'
    
    def get_project_count(self, obj):
        return obj.project_set.count()

class ProjectSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    scan_count = serializers.SerializerMethodField()
    finding_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = '__all__'
    
    def get_scan_count(self, obj):
        return obj.scantask_set.count()
    
    def get_finding_count(self, obj):
        return obj.finding_set.filter(active=True).count()

class ScanTaskSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    department_name = serializers.CharField(source='project.department.name', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ScanTask
        fields = '__all__'
    
    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            delta = obj.completed_at - obj.started_at
            return str(delta)
        return None

class FindingSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    department_name = serializers.CharField(source='project.department.name', read_only=True)
    severity_color = serializers.CharField(read_only=True)
    cwe_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Finding
        fields = '__all__'
    
    def get_cwe_info(self, obj):
        return obj.get_cwe_info()

class FindingDetailSerializer(FindingSerializer):
    """详细的漏洞序列化器，包含更多信息"""
    ai_analysis_summary = serializers.SerializerMethodField()
    source_context = serializers.JSONField(read_only=True)
    
    def get_ai_analysis_summary(self, obj):
        if obj.ai_analysis and obj.ai_analysis.get('success'):
            return {
                'has_analysis': True,
                'principle': obj.ai_analysis.get('principle', ''),
                'risk': obj.ai_analysis.get('risk', ''),
                'fix_suggestion': obj.ai_analysis.get('fix_suggestion', '')
            }
        return {'has_analysis': False}
```

## 🚀 部署和运行

### 1. 环境准备脚本

#### install.sh
```bash
#!/bin/bash

echo "开始安装智能代码安全分析平台..."

# 1. 检查Python版本
python3 --version || { echo "请先安装Python 3.8+"; exit 1; }

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装Python依赖
pip install -r requirements.txt

# 4. 创建必要目录
mkdir -p workspace/{projects,reports,scan_temp}
mkdir -p tools/{codeql,codeql-rules,jdk}
mkdir -p logs
mkdir -p static/{css,js}
mkdir -p media

# 5. 检查PostgreSQL
which psql || { echo "请先安装PostgreSQL"; exit 1; }

# 6. 创建数据库
sudo -u postgres createdb smart_security_analyzer 2>/dev/null || echo "数据库可能已存在"

# 7. 运行迁移
python manage.py migrate

# 8. 创建缓存表
python manage.py createcachetable

# 9. 创建超级用户
echo "创建管理员用户..."
python manage.py createsuperuser

# 10. 收集静态文件
python manage.py collectstatic --noinput

echo "安装完成！"
echo "请配置 .env 文件，然后运行: python manage.py runserver"
```

### 2. 启动脚本

#### start.sh
```bash
#!/bin/bash

# 激活虚拟环境
source venv/bin/activate

# 检查数据库连接
python manage.py check --database default

# 启动开发服务器
python manage.py runserver 0.0.0.0:7000
```

### 3. 生产部署脚本

#### start_daemon.sh
```bash
#!/bin/bash

# 激活虚拟环境
source venv/bin/activate

# 启动Gunicorn
gunicorn smart_security_analyzer.wsgi:application \
    --bind 0.0.0.0:7000 \
    --workers 4 \
    --worker-class sync \
    --timeout 300 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --daemon \
    --pid platform.pid \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info

echo "平台已启动，PID: $(cat platform.pid)"
```

## 📋 开发检查清单

### 阶段1：基础框架 (1-2天)
- [ ] Django项目初始化
- [ ] 数据库模型设计和迁移
- [ ] 基础管理后台配置
- [ ] 环境配置和.env文件
- [ ] 基础目录结构创建

### 阶段2：核心功能 (3-5天)
- [ ] 扫描队列系统实现
- [ ] Git仓库克隆功能
- [ ] 语言检测逻辑
- [ ] CodeQL扫描器集成
- [ ] Semgrep扫描器集成
- [ ] SARIF报告解析器

### 阶段3：API和前端 (2-3天)
- [ ] REST API接口实现
- [ ] 序列化器设计
- [ ] 基础前端模板
- [ ] 扫描任务监控页面
- [ ] 漏洞列表和详情页面

### 阶段4：增强功能 (2-3天)
- [ ] AI分析服务集成
- [ ] 翻译服务实现
- [ ] 统计报告生成
- [ ] 日志系统完善
- [ ] 错误处理和监控

### 阶段5：部署和优化 (1-2天)
- [ ] 部署脚本编写
- [ ] 性能优化
- [ ] 安全配置
- [ ] 文档完善
- [ ] 测试和调试

## 🔍 关键技术要点

### 1. 数据模型设计
- 借鉴DefectDojo的成熟设计
- 三级严重程度分级简化管理
- 完整的状态跟踪机制
- 灵活的JSON字段扩展

### 2. 扫描引擎架构
- 队列机制避免资源冲突
- 模块化扫描器设计
- 完善的进程管理
- 实时日志记录

### 3. AI集成策略
- 缓存机制提高效率
- 批量分析降低成本
- 错误处理保证稳定性
- 结构化结果解析

### 4. 部署考虑
- 相对路径便于迁移
- 环境变量灵活配置
- 跨平台兼容性
- 生产级别的安全配置

## 📚 参考资源

### 官方文档
- [Django官方文档](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [CodeQL文档](https://codeql.github.com/docs/)
- [Semgrep文档](https://semgrep.dev/docs/)

### 标准规范
- [SARIF规范](https://sarifweb.azurewebsites.net/)
- [CWE漏洞分类](https://cwe.mitre.org/)
- [CVSS评分标准](https://www.first.org/cvss/)

### 开源项目参考
- [DefectDojo](https://github.com/DefectDojo/django-DefectDojo)
- [OWASP ZAP](https://github.com/zaproxy/zaproxy)

---

**注意**：这个开发指南提供了完整的项目架构和实现细节。建议按照阶段性检查清单逐步实现，每个阶段完成后进行测试验证，确保功能正常后再进入下一阶段。