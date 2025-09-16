"""
智能代码安全分析平台 - 字段定义配置文件
用于集中管理所有模型的字段定义，方便扩展和维护
"""

# ==================== 通用字段定义 ====================

COMMON_FIELDS = {
    'created_at': 'models.DateTimeField(auto_now_add=True, verbose_name="创建时间")',
    'updated_at': 'models.DateTimeField(auto_now=True, verbose_name="更新时间")',
    'is_active': 'models.BooleanField(default=True, verbose_name="是否激活")',
    'description': 'models.TextField(blank=True, verbose_name="描述")',
    'notes': 'models.TextField(blank=True, verbose_name="备注")',
}

# ==================== 部门模型字段 ====================

DEPARTMENT_FIELDS = {
    'name': 'models.CharField(max_length=100, unique=True, verbose_name="部门名称")',
    'description': 'models.TextField(blank=True, verbose_name="部门描述")',
    'lead': 'models.CharField(max_length=100, blank=True, verbose_name="部门负责人")',
    'contact_email': 'models.EmailField(blank=True, verbose_name="联系邮箱")',
    'contact_phone': 'models.CharField(max_length=20, blank=True, verbose_name="联系电话")',
    'budget': 'models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="预算")',
    'location': 'models.CharField(max_length=200, blank=True, verbose_name="办公地点")',
    'parent_department': 'models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, verbose_name="上级部门")',
}

# ==================== 项目模型字段 ====================

PROJECT_FIELDS = {
    'name': 'models.CharField(max_length=200, verbose_name="项目名称")',
    'department': 'models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="所属部门")',
    'description': 'models.TextField(blank=True, verbose_name="项目描述")',
    'code_owner': 'models.CharField(max_length=100, verbose_name="代码负责人")',
    'tech_lead': 'models.CharField(max_length=100, blank=True, verbose_name="技术负责人")',
    'product_manager': 'models.CharField(max_length=100, blank=True, verbose_name="产品经理")',
    'source_path': 'models.CharField(max_length=1000, blank=True, verbose_name="源码路径")',
    'report_path': 'models.CharField(max_length=1000, blank=True, verbose_name="报告路径")',
    'repository_url': 'models.URLField(blank=True, verbose_name="代码仓库")',
    'business_criticality': 'models.CharField(max_length=20, choices=BUSINESS_CRITICALITY_CHOICES, default="medium", verbose_name="业务重要性")',
    'lifecycle': 'models.CharField(max_length=20, choices=LIFECYCLE_CHOICES, default="development", verbose_name="生命周期")',
    'platform': 'models.CharField(max_length=50, blank=True, verbose_name="平台")',
    'language': 'models.CharField(max_length=100, blank=True, verbose_name="主要编程语言")',
    'framework': 'models.CharField(max_length=100, blank=True, verbose_name="技术框架")',
    'version': 'models.CharField(max_length=50, blank=True, verbose_name="版本号")',
    'start_date': 'models.DateField(null=True, blank=True, verbose_name="项目开始日期")',
    'end_date': 'models.DateField(null=True, blank=True, verbose_name="项目结束日期")',
    'budget': 'models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="项目预算")',
    'team_size': 'models.IntegerField(null=True, blank=True, verbose_name="团队规模")',
}

# ==================== 扫描任务模型字段 ====================

SCAN_TASK_FIELDS = {
    'project': 'models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="项目")',
    'tool_name': 'models.CharField(max_length=50, choices=TOOL_CHOICES, verbose_name="扫描工具")',
    'scan_type': 'models.CharField(max_length=30, verbose_name="扫描类型")',
    'status': 'models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="状态")',
    'report_file': 'models.CharField(max_length=1000, blank=True, verbose_name="报告文件路径")',
    'file_size': 'models.BigIntegerField(null=True, blank=True, verbose_name="文件大小")',
    'scan_config': 'models.JSONField(default=dict, verbose_name="扫描配置")',
    'total_findings': 'models.IntegerField(default=0, verbose_name="发现总数")',
    'critical_count': 'models.IntegerField(default=0, verbose_name="严重漏洞数")',
    'high_count': 'models.IntegerField(default=0, verbose_name="高危漏洞数")',
    'medium_count': 'models.IntegerField(default=0, verbose_name="中危漏洞数")',
    'low_count': 'models.IntegerField(default=0, verbose_name="低危漏洞数")',
    'info_count': 'models.IntegerField(default=0, verbose_name="信息漏洞数")',
    'started_at': 'models.DateTimeField(null=True, blank=True, verbose_name="开始时间")',
    'completed_at': 'models.DateTimeField(null=True, blank=True, verbose_name="完成时间")',
    'error_message': 'models.TextField(blank=True, verbose_name="错误信息")',
    'scan_duration': 'models.DurationField(null=True, blank=True, verbose_name="扫描耗时")',
    'triggered_by': 'models.CharField(max_length=100, blank=True, verbose_name="触发者")',
    'branch': 'models.CharField(max_length=100, blank=True, verbose_name="代码分支")',
    'commit_hash': 'models.CharField(max_length=40, blank=True, verbose_name="提交哈希")',
}

# ==================== 漏洞发现模型字段 ====================

FINDING_FIELDS = {
    'project': 'models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="项目")',
    'scan_task': 'models.ForeignKey(ScanTask, on_delete=models.CASCADE, verbose_name="扫描任务")',
    'title': 'models.CharField(max_length=500, verbose_name="漏洞标题")',
    'description': 'models.TextField(verbose_name="漏洞描述")',
    'description_zh': 'models.TextField(blank=True, verbose_name="中文描述")',
    'severity': 'models.CharField(max_length=20, choices=SEVERITY_CHOICES, verbose_name="严重程度")',
    'confidence': 'models.CharField(max_length=20, choices=CONFIDENCE_CHOICES, default="medium", verbose_name="置信度")',
    'cwe': 'models.CharField(max_length=20, blank=True, verbose_name="CWE编号")',
    'cve': 'models.CharField(max_length=50, blank=True, verbose_name="CVE编号")',
    'cvss_score': 'models.FloatField(null=True, blank=True, verbose_name="CVSS评分")',
    'cvss_vector': 'models.CharField(max_length=200, blank=True, verbose_name="CVSS向量")',
    'owasp_top10': 'models.CharField(max_length=10, blank=True, verbose_name="OWASP Top 10")',
    'file_path': 'models.CharField(max_length=1000, verbose_name="文件路径")',
    'line_number': 'models.IntegerField(null=True, blank=True, verbose_name="行号")',
    'column_number': 'models.IntegerField(null=True, blank=True, verbose_name="列号")',
    'code_snippet': 'models.TextField(blank=True, verbose_name="代码片段")',
    'status': 'models.CharField(max_length=20, choices=FINDING_STATUS_CHOICES, default="new", verbose_name="状态")',
    'false_positive': 'models.BooleanField(default=False, verbose_name="误报")',
    'risk_accepted': 'models.BooleanField(default=False, verbose_name="风险接受")',
    'out_of_scope': 'models.BooleanField(default=False, verbose_name="超出范围")',
    'duplicate': 'models.BooleanField(default=False, verbose_name="重复")',
    'active': 'models.BooleanField(default=True, verbose_name="激活状态")',
    'verified': 'models.BooleanField(default=False, verbose_name="已验证")',
    'mitigation': 'models.TextField(blank=True, verbose_name="缓解措施")',
    'impact': 'models.TextField(blank=True, verbose_name="影响分析")',
    'references': 'models.TextField(blank=True, verbose_name="参考链接")',
    'tags': 'models.CharField(max_length=500, blank=True, verbose_name="标签")',
    'component_name': 'models.CharField(max_length=200, blank=True, verbose_name="组件名称")',
    'component_version': 'models.CharField(max_length=100, blank=True, verbose_name="组件版本")',
    'found_by': 'models.CharField(max_length=100, blank=True, verbose_name="发现者")',
    'assignee': 'models.CharField(max_length=100, blank=True, verbose_name="指派给")',
    'due_date': 'models.DateField(null=True, blank=True, verbose_name="截止日期")',
    'last_reviewed': 'models.DateTimeField(null=True, blank=True, verbose_name="最后审查时间")',
    'last_reviewed_by': 'models.CharField(max_length=100, blank=True, verbose_name="最后审查者")',
    'sla_start_date': 'models.DateTimeField(null=True, blank=True, verbose_name="SLA开始时间")',
    'sla_deadline': 'models.DateTimeField(null=True, blank=True, verbose_name="SLA截止时间")',
    'effort_for_fixing': 'models.CharField(max_length=20, blank=True, verbose_name="修复工作量")',
    'sonarqube_issue': 'models.CharField(max_length=100, blank=True, verbose_name="SonarQube问题ID")',
    'unique_id_from_tool': 'models.CharField(max_length=200, blank=True, verbose_name="工具唯一ID")',
    'vuln_id_from_tool': 'models.CharField(max_length=200, blank=True, verbose_name="工具漏洞ID")',
    'sast_source_object': 'models.CharField(max_length=200, blank=True, verbose_name="SAST源对象")',
    'sast_sink_object': 'models.CharField(max_length=200, blank=True, verbose_name="SAST汇聚对象")',
    'sast_source_line': 'models.IntegerField(null=True, blank=True, verbose_name="SAST源行号")',
    'sast_source_file_path': 'models.CharField(max_length=1000, blank=True, verbose_name="SAST源文件路径")',
    'nb_occurences': 'models.IntegerField(null=True, blank=True, verbose_name="出现次数")',
    'publish_date': 'models.DateTimeField(null=True, blank=True, verbose_name="发布日期")',
    'service': 'models.CharField(max_length=200, blank=True, verbose_name="服务")',
    'planned_remediation_date': 'models.DateField(null=True, blank=True, verbose_name="计划修复日期")',
    'planned_remediation_version': 'models.CharField(max_length=100, blank=True, verbose_name="计划修复版本")',
    'reporter': 'models.CharField(max_length=100, blank=True, verbose_name="报告者")',
    'is_mitigated': 'models.BooleanField(default=False, verbose_name="已缓解")',
    'thread_id': 'models.IntegerField(null=True, blank=True, verbose_name="线程ID")',
    'scanner_confidence': 'models.IntegerField(null=True, blank=True, verbose_name="扫描器置信度")',
    'hash_code': 'models.CharField(max_length=64, blank=True, verbose_name="哈希码")',
    'ai_analysis': 'models.TextField(blank=True, verbose_name="AI分析结果")',
    'ai_fix_suggestion': 'models.TextField(blank=True, verbose_name="AI修复建议")',
}

# ==================== 漏洞备注模型字段 ====================

FINDING_NOTE_FIELDS = {
    'finding': 'models.ForeignKey(Finding, on_delete=models.CASCADE, verbose_name="漏洞")',
    'author': 'models.CharField(max_length=100, verbose_name="作者")',
    'note': 'models.TextField(verbose_name="备注内容")',
    'private': 'models.BooleanField(default=False, verbose_name="私有备注")',
    'note_type': 'models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES, default="comment", verbose_name="备注类型")',
}

# ==================== 状态历史模型字段 ====================

STATUS_HISTORY_FIELDS = {
    'finding': 'models.ForeignKey(Finding, on_delete=models.CASCADE, verbose_name="漏洞")',
    'old_status': 'models.CharField(max_length=20, verbose_name="原状态")',
    'new_status': 'models.CharField(max_length=20, verbose_name="新状态")',
    'changed_by': 'models.CharField(max_length=100, verbose_name="修改者")',
    'change_reason': 'models.TextField(blank=True, verbose_name="修改原因")',
}

# ==================== 选择项定义 ====================

CHOICES = {
    'BUSINESS_CRITICALITY_CHOICES': [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('critical', '关键')
    ],
    
    'LIFECYCLE_CHOICES': [
        ('development', '开发中'),
        ('testing', '测试中'),
        ('staging', '预发布'),
        ('production', '生产环境'),
        ('maintenance', '维护中'),
        ('deprecated', '已废弃')
    ],
    
    'TOOL_CHOICES': [
        ('codeql', 'CodeQL'),
        ('semgrep', 'Semgrep'),
        ('sonarqube', 'SonarQube'),
        ('checkmarx', 'Checkmarx'),
        ('veracode', 'Veracode'),
        ('bandit', 'Bandit'),
        ('eslint', 'ESLint'),
        ('brakeman', 'Brakeman'),
        ('gosec', 'Gosec'),
        ('safety', 'Safety'),
    ],
    
    'STATUS_CHOICES': [
        ('pending', '待处理'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ],
    
    'SEVERITY_CHOICES': [
        ('Critical', '严重'),
        ('High', '高危'),
        ('Medium', '中危'),
        ('Low', '低危'),
        ('Info', '信息'),
    ],
    
    'CONFIDENCE_CHOICES': [
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    ],
    
    'FINDING_STATUS_CHOICES': [
        ('new', '新发现'),
        ('active', '激活'),
        ('verified', '已验证'),
        ('false_positive', '误报'),
        ('out_of_scope', '超出范围'),
        ('duplicate', '重复'),
        ('risk_accepted', '风险接受'),
        ('fixed', '已修复'),
        ('mitigated', '已缓解'),
        ('under_review', '审查中'),
        ('reopened', '重新打开'),
    ],
    
    'NOTE_TYPE_CHOICES': [
        ('comment', '评论'),
        ('fix_attempt', '修复尝试'),
        ('mitigation', '缓解措施'),
        ('false_positive_justification', '误报说明'),
        ('risk_acceptance', '风险接受'),
    ],
}

# ==================== 扩展字段建议 ====================

EXTENSION_SUGGESTIONS = {
    'Department': [
        'cost_center',  # 成本中心
        'security_contact',  # 安全联系人
        'compliance_requirements',  # 合规要求
    ],
    
    'Project': [
        'security_champion',  # 安全冠军
        'data_classification',  # 数据分类
        'compliance_framework',  # 合规框架
        'deployment_frequency',  # 部署频率
        'user_count',  # 用户数量
        'revenue_impact',  # 收入影响
    ],
    
    'Finding': [
        'exploit_maturity',  # 漏洞利用成熟度
        'remediation_cost',  # 修复成本
        'business_impact_score',  # 业务影响评分
        'attack_vector',  # 攻击向量
        'attack_complexity',  # 攻击复杂度
        'privileges_required',  # 所需权限
        'user_interaction',  # 用户交互
        'scope_change',  # 范围变化
    ],
}

# ==================== 使用说明 ====================

USAGE_INSTRUCTIONS = """
使用说明：

1. 查看字段定义：
   - 所有字段定义都在对应的字典中
   - 字段名作为key，字段定义作为value

2. 添加新字段：
   - 在对应模型的字段字典中添加新字段
   - 在CHOICES中添加相关选择项
   - 在EXTENSION_SUGGESTIONS中记录扩展建议

3. 字段命名规范：
   - 使用小写字母和下划线
   - 布尔字段以is_、has_、can_等开头
   - 时间字段以_at、_date结尾
   - 外键字段不加_id后缀

4. 常用字段类型：
   - CharField: 短文本
   - TextField: 长文本
   - IntegerField: 整数
   - FloatField: 浮点数
   - BooleanField: 布尔值
   - DateTimeField: 日期时间
   - DateField: 日期
   - JSONField: JSON数据
   - ForeignKey: 外键关系

5. 扩展时参考：
   - 查看EXTENSION_SUGGESTIONS获取建议
   - 保持字段命名一致性
   - 添加适当的verbose_name
   - 考虑字段的默认值和约束
"""
