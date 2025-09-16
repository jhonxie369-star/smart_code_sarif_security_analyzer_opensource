from rest_framework import serializers
from core.models import Department, Project, ScanTask, Finding, FindingNote, StatusHistory


class DepartmentSerializer(serializers.ModelSerializer):
    """部门序列化器"""
    project_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'lead', 'project_count', 'created_at', 'updated_at']
    
    def get_project_count(self, obj):
        return obj.project_set.filter(is_active=True).count()


class ProjectSerializer(serializers.ModelSerializer):
    """项目序列化器"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    finding_count = serializers.SerializerMethodField()
    last_scan = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'department', 'department_name', 'description',
            'code_owner', 'tech_lead', 'source_path', 'report_path', 
            'repository_url', 'git_url', 'git_branch', 'auto_scan_enabled',
            'business_criticality', 'tags', 'metadata', 'is_active', 
            'finding_count', 'last_scan', 'created_at', 'updated_at'
        ]
    
    def get_finding_count(self, obj):
        return obj.finding_set.filter(active=True).count()
    
    def get_last_scan(self, obj):
        last_scan = obj.scantask_set.order_by('-created_at').first()
        if last_scan:
            return {
                'id': last_scan.id,
                'tool_name': last_scan.tool_name,
                'status': last_scan.status,
                'total_findings': last_scan.total_findings,
                'created_at': last_scan.created_at
            }
        return None


class ScanTaskSerializer(serializers.ModelSerializer):
    """扫描任务序列化器"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    department_name = serializers.CharField(source='project.department.name', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ScanTask
        fields = [
            'id', 'project', 'project_name', 'department_name', 'tool_name', 
            'scan_type', 'status', 'report_file', 'file_size', 'scan_config',
            'total_findings', 'critical_count', 'high_count', 'medium_count', 
            'low_count', 'info_count', 'started_at', 'completed_at', 'duration',
            'error_message', 'created_at', 'updated_at'
        ]
    
    def get_duration(self, obj):
        if obj.duration:
            return str(obj.duration)
        return None


class FindingSerializer(serializers.ModelSerializer):
    """漏洞发现序列化器（列表视图）"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    department_name = serializers.CharField(source='project.department.name', read_only=True)
    severity_color = serializers.CharField(read_only=True)
    sla_days_remaining = serializers.SerializerMethodField()
    has_ai_analysis = serializers.SerializerMethodField()
    
    class Meta:
        model = Finding
        fields = [
            'id', 'title', 'severity', 'severity_color', 'numerical_severity',
            'project', 'project_name', 'department_name', 'file_path', 'line_number',
            'message', 'translated_message', 'active', 'verified', 'false_p',
            'duplicate', 'is_mitigated', 'risk_accepted', 'code_owner',
            'sla_days_remaining', 'has_ai_analysis', 'date', 'created_at'
        ]
    
    def get_sla_days_remaining(self, obj):
        return obj.get_sla_days_remaining()
    
    def get_has_ai_analysis(self, obj):
        return bool(obj.ai_analysis)


class FindingDetailSerializer(serializers.ModelSerializer):
    """漏洞发现详细序列化器"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    department_name = serializers.CharField(source='project.department.name', read_only=True)
    severity_color = serializers.CharField(read_only=True)
    sla_days_remaining = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    status_history = serializers.SerializerMethodField()
    
    class Meta:
        model = Finding
        fields = [
            'id', 'title', 'description', 'message', 'translated_message',
            'severity', 'severity_color', 'numerical_severity', 'cvssv3', 'cvssv3_score',
            'cwe', 'file_path', 'line_number', 'column_number', 'source_context',
            'project', 'project_name', 'department_name', 'scan_task',
            'active', 'verified', 'false_p', 'duplicate', 'out_of_scope',
            'risk_accepted', 'under_review', 'is_mitigated', 'mitigated',
            'last_reviewed', 'last_status_update', 'code_owner', 'assigned_to',
            'reporter', 'ai_analysis', 'ai_cached', 'tags', 'metadata',
            'vuln_id_from_tool', 'unique_id_from_tool', 'sla_days_remaining',
            'notes', 'status_history', 'date', 'created_at', 'updated_at'
        ]
    
    def get_sla_days_remaining(self, obj):
        return obj.get_sla_days_remaining()
    
    def get_notes(self, obj):
        notes = obj.notes.order_by('-created_at')[:5]  # 最近5条备注
        return FindingNoteSerializer(notes, many=True).data
    
    def get_status_history(self, obj):
        history = obj.status_history.order_by('-created_at')[:10]  # 最近10条历史
        return StatusHistorySerializer(history, many=True).data


class FindingNoteSerializer(serializers.ModelSerializer):
    """漏洞备注序列化器"""
    author_name = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = FindingNote
        fields = ['id', 'content', 'author', 'author_name', 'is_private', 'created_at', 'updated_at']


class StatusHistorySerializer(serializers.ModelSerializer):
    """状态历史序列化器"""
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True)
    
    class Meta:
        model = StatusHistory
        fields = ['id', 'from_status', 'to_status', 'changed_by', 'changed_by_name', 'reason', 'created_at']


class FindingCreateSerializer(serializers.ModelSerializer):
    """创建漏洞序列化器"""
    
    class Meta:
        model = Finding
        fields = [
            'title', 'description', 'message', 'severity', 'file_path', 
            'line_number', 'column_number', 'project', 'scan_task',
            'code_owner', 'cwe', 'cvssv3', 'cvssv3_score', 'tags'
        ]
    
    def create(self, validated_data):
        # 自动设置一些字段
        validated_data['reporter'] = self.context['request'].user.username
        validated_data['date'] = timezone.now().date()
        
        # 翻译消息
        from translation.services import translation_service
        if translation_service.is_available():
            validated_data['translated_message'] = translation_service.translate_text(
                validated_data['message']
            )
        
        return super().create(validated_data)


class FindingUpdateSerializer(serializers.ModelSerializer):
    """更新漏洞序列化器"""
    
    class Meta:
        model = Finding
        fields = [
            'title', 'description', 'severity', 'active', 'verified', 
            'false_p', 'duplicate', 'out_of_scope', 'risk_accepted',
            'under_review', 'is_mitigated', 'code_owner', 'assigned_to',
            'tags', 'metadata'
        ]


class ScanTaskCreateSerializer(serializers.ModelSerializer):
    """创建扫描任务序列化器"""
    
    class Meta:
        model = ScanTask
        fields = [
            'project', 'tool_name', 'scan_type', 'report_file', 
            'scan_config'
        ]
    
    def create(self, validated_data):
        validated_data['status'] = 'pending'
        return super().create(validated_data)


class ProjectCreateSerializer(serializers.ModelSerializer):
    """创建项目序列化器"""
    
    class Meta:
        model = Project
        fields = [
            'name', 'department', 'description', 'code_owner', 'tech_lead',
            'source_path', 'report_path', 'repository_url', 'business_criticality',
            'tags', 'metadata'
        ]


class StatisticsSerializer(serializers.Serializer):
    """统计信息序列化器"""
    severity_stats = serializers.DictField()
    status_stats = serializers.DictField()
    sla_stats = serializers.DictField()
    
    def to_representation(self, instance):
        return instance


class TrendDataSerializer(serializers.Serializer):
    """趋势数据序列化器"""
    date = serializers.DateField()
    new_findings = serializers.DictField()
    fixed_count = serializers.IntegerField()
    active_count = serializers.IntegerField()


class AIAnalysisResultSerializer(serializers.Serializer):
    """AI分析结果序列化器"""
    analysis = serializers.DictField()
    cached = serializers.BooleanField()
    timestamp = serializers.DateTimeField()
    error = serializers.CharField(required=False)


class TranslationResultSerializer(serializers.Serializer):
    """翻译结果序列化器"""
    original = serializers.CharField()
    translated = serializers.CharField()
    cached = serializers.BooleanField()
    error = serializers.CharField(required=False)



