import os
import json
from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.urls import reverse


class SeverityManager:
    """严重程度管理器 - 借鉴DefectDojo的分级逻辑"""
    
    # 三级严重程度分级
    SEVERITY_CHOICES = (
        ("低危", "低危"), 
        ("中危", "中危"),
        ("高危", "高危")
    )
    
    SEVERITIES = [s[0] for s in SEVERITY_CHOICES]
    
    # 数值映射 - 用于排序和统计
    NUMERICAL_SEVERITY = {
        "低危": "S1", 
        "中危": "S2",
        "高危": "S3"
    }
    
    # 颜色映射
    SEVERITY_COLORS = {
        "高危": "#dc3545",  # 红色
        "中危": "#ffc107",  # 黄色
        "低危": "#28a745"   # 绿色
    }
    
    @classmethod
    def cvss_to_severity(cls, cvss_score: float) -> str:
        """CVSS分数转严重程度 - 三级分级"""
        # Critical -> 高危
        if cvss_score >= 9:
            return "高危"
        # High -> 中危
        elif cvss_score >= 7:
            return "中危"
        # Medium/Low/Info -> 低危
        else:
            return "低危"
    
    @classmethod
    def sarif_level_to_severity(cls, level: str) -> str:
        """SARIF级别转严重程度 - 三级分级"""
        # error -> 中危
        if level == "error":
            return "中危"
        # warning/note/info -> 低危
        else:
            return "低危"  # 默认值
    
    @classmethod
    def get_numerical_severity(cls, severity: str) -> str:
        """获取数值严重程度"""
        return cls.NUMERICAL_SEVERITY.get(severity, "S1")  # 默认低危
    
    @classmethod
    def get_severity_color(cls, severity: str) -> str:
        """获取严重程度颜色"""
        return cls.SEVERITY_COLORS.get(severity, "#6c757d")


class Department(models.Model):
    """部门模型"""
    name = models.CharField(max_length=100, unique=True, verbose_name="部门名称")
    description = models.TextField(blank=True, verbose_name="部门描述")
    lead = models.CharField(max_length=100, blank=True, verbose_name="部门负责人")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "部门"
        verbose_name_plural = "部门"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            try:
                from django.conf import settings
                import os
                
                dept_project_dir = os.path.join(settings.AUTO_SCAN_CONFIG['PROJECT_DIR'], self.name)
                dept_report_dir = os.path.join(settings.AUTO_SCAN_CONFIG['OUTPUT_DIR'], self.name)
                
                os.makedirs(dept_project_dir, exist_ok=True)
                os.makedirs(dept_report_dir, exist_ok=True)
                
            except Exception:
                pass  # 静默处理，避免影响正常保存
    
    def delete(self, *args, **kwargs):
        try:
            from django.conf import settings
            import subprocess
            
            # 清理部门目录
            dept_project_dir = os.path.join(settings.AUTO_SCAN_CONFIG['PROJECT_DIR'], self.name)
            dept_report_dir = os.path.join(settings.AUTO_SCAN_CONFIG['OUTPUT_DIR'], self.name)
            
            subprocess.run(f"rm -rf '{dept_project_dir}' 2>/dev/null || true", shell=True)
            subprocess.run(f"rm -rf '{dept_report_dir}' 2>/dev/null || true", shell=True)
            
        except Exception:
            pass
        
        super().delete(*args, **kwargs)


class Project(models.Model):
    """项目模型 - 支持部门/项目结构"""
    name = models.CharField(max_length=200, verbose_name="项目名称")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="所属部门")
    description = models.TextField(blank=True, verbose_name="项目描述")
    
    # 负责人信息
    code_owner = models.CharField(max_length=100, verbose_name="代码负责人")
    tech_lead = models.CharField(max_length=100, blank=True, verbose_name="技术负责人")
    
    # 路径配置
    source_path = models.CharField(max_length=1000, blank=True, verbose_name="源码路径")
    report_path = models.CharField(max_length=1000, blank=True, verbose_name="报告路径")
    repository_url = models.CharField(max_length=500, blank=True, verbose_name="代码仓库")
    
    # Git配置
    git_url = models.CharField(max_length=500, blank=True, verbose_name="Git仓库地址")
    git_branch = models.CharField(max_length=100, default='master', blank=True, verbose_name="Git分支")
    auto_scan_enabled = models.BooleanField(default=False, verbose_name="启用自动扫描")
    
    # 业务属性
    business_criticality = models.CharField(
        max_length=20, 
        choices=[
            ('low', '低'),
            ('medium', '中'),
            ('high', '高'),
            ('critical', '关键')
        ],
        default='medium',
        blank=True,
        verbose_name="业务重要性"
    )
    
    # 编译命令配置
    build_command = models.TextField(blank=True, verbose_name="编译命令", help_text="留空使用默认命令")
    
    # 扩展字段
    tags = models.JSONField(default=list, blank=True, verbose_name="标签")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="扩展信息")
    
    # 状态
    is_active = models.BooleanField(default=True, verbose_name="是否活跃")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "项目"
        verbose_name_plural = "项目"
        unique_together = ['department', 'name']
        ordering = ['department__name', 'name']
    
    def __str__(self):
        return f"{self.department.name}/{self.name}"
    
    def get_absolute_url(self):
        return reverse('project-detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            try:
                from django.conf import settings
                import os
                
                project_dir = os.path.join(settings.AUTO_SCAN_CONFIG['PROJECT_DIR'], self.department.name, self.name)
                report_dir = os.path.join(settings.AUTO_SCAN_CONFIG['OUTPUT_DIR'], self.department.name, self.name)
                
                os.makedirs(project_dir, exist_ok=True)
                os.makedirs(report_dir, exist_ok=True)
                
            except Exception:
                pass  # 静默处理，避免影响正常保存
    
    def delete(self, *args, **kwargs):
        try:
            from django.conf import settings
            import subprocess
            
            # 清理项目目录
            project_dir = os.path.join(settings.AUTO_SCAN_CONFIG['PROJECT_DIR'], self.department.name, self.name)
            report_dir = os.path.join(settings.AUTO_SCAN_CONFIG['OUTPUT_DIR'], self.department.name, self.name)
            temp_dir = os.path.join(settings.AUTO_SCAN_CONFIG['WORK_DIR'], f'scan_{self.id}')
            
            subprocess.run(f"rm -rf '{project_dir}' 2>/dev/null || true", shell=True)
            subprocess.run(f"rm -rf '{report_dir}' 2>/dev/null || true", shell=True)
            subprocess.run(f"rm -rf '{temp_dir}' 2>/dev/null || true", shell=True)
            
        except Exception:
            pass
        
        super().delete(*args, **kwargs)


class ScanTask(models.Model):
    """扫描任务模型"""
    
    TOOL_CHOICES = [
        ('codeql', 'CodeQL'),
        ('semgrep', 'Semgrep'),
        ('sonarqube', 'SonarQube'),
        ('checkmarx', 'Checkmarx'),
        ('veracode', 'Veracode'),
        ('auto', '自动扫描'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="项目")
    tool_name = models.CharField(max_length=50, choices=TOOL_CHOICES, verbose_name="扫描工具")
    scan_type = models.CharField(max_length=30, verbose_name="扫描类型")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="状态")
    
    # 文件信息
    report_file = models.CharField(max_length=1000, blank=True, verbose_name="报告文件路径")
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name="文件大小")
    
    # 扫描配置
    scan_config = models.JSONField(default=dict, verbose_name="扫描配置")
    
    # 统计信息
    total_findings = models.IntegerField(default=0, verbose_name="发现总数")
    critical_count = models.IntegerField(default=0, verbose_name="严重漏洞数")
    high_count = models.IntegerField(default=0, verbose_name="高危漏洞数")
    medium_count = models.IntegerField(default=0, verbose_name="中危漏洞数")
    low_count = models.IntegerField(default=0, verbose_name="低危漏洞数")
    info_count = models.IntegerField(default=0, verbose_name="信息漏洞数")
    
    # 时间信息
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 错误信息
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    
    # 扫描日志
    scan_log = models.TextField(blank=True, verbose_name="扫描日志")
    
    class Meta:
        verbose_name = "扫描任务"
        verbose_name_plural = "扫描任务"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.project} - {self.tool_name} - {self.status}"
    
    @property
    def duration(self):
        """计算扫描耗时"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class Finding(models.Model):
    """漏洞发现模型 - 借鉴DefectDojo的完整设计"""
    
    # 基础信息 - 只保留最核心的字段为必填
    title = models.CharField(max_length=511, verbose_name="标题")
    date = models.DateField(default=timezone.now, verbose_name="发现日期")
    
    # 严重程度相关 - 设置默认值，允许为空
    severity = models.CharField(
        max_length=200, 
        choices=SeverityManager.SEVERITY_CHOICES,
        default='Info',
        blank=True,
        verbose_name="严重程度"
    )
    numerical_severity = models.CharField(
        max_length=4, 
        blank=True,
        verbose_name="数值严重程度"
    )
    
    # CVSS相关 - 全部可选
    cvssv3 = models.TextField(
        max_length=117, 
        null=True, 
        blank=True,
        verbose_name="CVSS v3向量"
    )
    cvssv3_score = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        verbose_name="CVSS v3分数"
    )
    
    # CWE分类 - 可选
    cwe = models.IntegerField(
        default=0, 
        null=True, 
        blank=True,
        verbose_name="CWE编号"
    )
    
    # 描述信息 - 允许为空
    description = models.TextField(blank=True, verbose_name="漏洞描述")
    message = models.TextField(blank=True, verbose_name="原始消息")
    translated_message = models.TextField(blank=True, verbose_name="中文描述")
    
    # 位置信息 - 文件路径和行号可选
    file_path = models.CharField(max_length=1000, blank=True, verbose_name="文件路径")
    line_number = models.IntegerField(null=True, blank=True, verbose_name="行号")
    column_number = models.IntegerField(null=True, blank=True, verbose_name="列号")
    
    # 状态管理 - 借鉴DefectDojo的完整状态系统
    active = models.BooleanField(default=True, verbose_name="活跃状态")
    verified = models.BooleanField(default=False, verbose_name="已验证")
    false_p = models.BooleanField(default=False, verbose_name="误报")
    duplicate = models.BooleanField(default=False, verbose_name="重复")
    out_of_scope = models.BooleanField(default=False, verbose_name="超出范围")
    risk_accepted = models.BooleanField(default=False, verbose_name="风险接受")
    under_review = models.BooleanField(default=False, verbose_name="审核中")
    is_mitigated = models.BooleanField(default=False, verbose_name="已缓解")
    
    # 时间戳
    mitigated = models.DateTimeField(null=True, blank=True, verbose_name="缓解时间")
    last_reviewed = models.DateTimeField(null=True, blank=True, verbose_name="最后审核时间")
    last_status_update = models.DateTimeField(auto_now=True, verbose_name="状态更新时间")
    
    # 责任人 - 全部可选
    code_owner = models.CharField(max_length=100, blank=True, verbose_name="代码负责人")
    assigned_to = models.CharField(max_length=100, blank=True, verbose_name="分配给")
    reporter = models.CharField(max_length=100, blank=True, verbose_name="报告人")
    
    # AI分析结果 - 继承您的AI功能
    ai_analysis = models.JSONField(default=dict, verbose_name="AI分析结果")
    ai_cached = models.BooleanField(default=False, verbose_name="AI结果缓存")
    ai_analyzing = models.BooleanField(default=False, verbose_name="AI分析中")
    
    # AI分析效果评估
    AI_QUALITY_CHOICES = [
        ('', '未评估'),
        ('excellent', '完整正确，可以直接用'),
        ('good', '建议正确，但是不能直接用'),
        ('poor', '建议错误'),
    ]
    ai_quality_rating = models.CharField(
        max_length=20,
        choices=AI_QUALITY_CHOICES,
        blank=True,
        verbose_name="AI分析质量评级"
    )
    ai_quality_comment = models.TextField(
        blank=True,
        verbose_name="AI质量评估备注"
    )
    ai_rated_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_ratings',
        verbose_name="评估人"
    )
    ai_rated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="评估时间"
    )
    
    # 源码上下文 - 继承您的源码展示功能
    source_context = models.JSONField(default=dict, verbose_name="源码上下文")
    
    # 扩展字段 - 元数据设置为可选
    tags = models.JSONField(default=list, blank=True, verbose_name="标签")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="元数据")
    
    # 手动扫描标记
    manual_scan = models.BooleanField(default=False, verbose_name="手动扫描")
    
    # 工具相关 - 保持可选
    vuln_id_from_tool = models.CharField(max_length=200, blank=True, verbose_name="工具漏洞ID")
    unique_id_from_tool = models.CharField(max_length=200, blank=True, verbose_name="工具唯一ID")
    
    # 关联 - 允许为空以便灵活保存
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, verbose_name="项目")
    scan_task = models.ForeignKey(ScanTask, on_delete=models.CASCADE, null=True, blank=True, verbose_name="扫描任务")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "漏洞发现"
        verbose_name_plural = "漏洞发现"
        ordering = ['-numerical_severity', '-date']
        indexes = [
            models.Index(fields=['severity', 'active']),
            models.Index(fields=['project', 'severity']),
            models.Index(fields=['scan_task', 'active']),
            models.Index(fields=['file_path', 'line_number']),
        ]
    
    def save(self, *args, **kwargs):
        """保存时自动设置数值严重程度"""
        self.numerical_severity = SeverityManager.get_numerical_severity(self.severity)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - {self.severity}"
    
    @property
    def severity_color(self):
        """获取严重程度颜色"""
        return SeverityManager.get_severity_color(self.severity)
    
    def get_sla_days_remaining(self):
        """获取SLA剩余天数 - 借鉴DefectDojo"""
        sla_days = {
            "Critical": 7,
            "High": 30,
            "Medium": 90,
            "Low": 180,
            "Info": 365
        }
        
        target_days = sla_days.get(self.severity, 90)
        days_since_found = (timezone.now().date() - self.date).days
        return max(0, target_days - days_since_found)
    
    def get_absolute_url(self):
        return reverse('finding-detail', kwargs={'pk': self.pk})
    
    def get_cwe_info(self):
        """获取CWE详细信息"""
        if self.cwe:
            from .cwe_utils import CWEExplainer
            return CWEExplainer.get_cwe_info(self.cwe)
        return None


class FindingNote(models.Model):
    """漏洞备注模型"""
    finding = models.ForeignKey(Finding, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="作者")
    content = models.TextField(verbose_name="备注内容")
    is_private = models.BooleanField(default=False, verbose_name="私有备注")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "漏洞备注"
        verbose_name_plural = "漏洞备注"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.finding.title} - {self.author.username}"


class StatusHistory(models.Model):
    """状态变更历史"""
    finding = models.ForeignKey(Finding, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=50, verbose_name="原状态")
    to_status = models.CharField(max_length=50, verbose_name="新状态")
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="操作人")
    reason = models.TextField(blank=True, verbose_name="变更原因")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "状态历史"
        verbose_name_plural = "状态历史"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.finding.title}: {self.from_status} -> {self.to_status}"
