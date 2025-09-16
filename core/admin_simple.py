from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Department, Project, ScanTask, Finding, FindingNote, StatusHistory


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'lead', 'project_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description', 'lead']
    ordering = ['name']
    
    def project_count(self, obj):
        count = obj.project_set.count()
        url = reverse('admin:core_project_changelist') + f'?department__id__exact={obj.id}'
        return format_html('<a href="{}">{} 个项目</a>', url, count)
    project_count.short_description = '项目数量'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'code_owner', 'business_criticality', 'finding_count', 'is_active', 'created_at']
    list_filter = ['department', 'business_criticality', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'code_owner', 'tech_lead']
    ordering = ['department__name', 'name']
    
    def finding_count(self, obj):
        count = obj.finding_set.filter(active=True).count()
        url = reverse('admin:core_finding_changelist') + f'?project__id__exact={obj.id}&active__exact=1'
        return format_html('<a href="{}">{} 个活跃漏洞</a>', url, count)
    finding_count.short_description = '活跃漏洞'


@admin.register(ScanTask)
class ScanTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'project', 'tool_name', 'status', 'total_findings', 'created_at']
    list_filter = ['tool_name', 'status', 'created_at']
    search_fields = ['project__name', 'tool_name']
    ordering = ['-created_at']


@admin.register(Finding)
class FindingAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity_badge', 'project', 'file_path', 'line_number', 'status_badges', 'code_owner', 'date']
    list_filter = ['severity', 'active', 'verified', 'false_p', 'is_mitigated', 'project__department', 'date']
    search_fields = ['title', 'description', 'file_path', 'code_owner', 'message']
    ordering = ['-numerical_severity', '-date']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'severity', 'date', 'file_path', 'line_number', 'cwe', 'cvssv3_score', 'description', 'translated_message', 'code_owner')
        }),
        ('源码和分析', {
            'fields': ('source_context_display', 'ai_analysis_display')
        }),
        ('状态管理', {
            'fields': ('status_radio_group',)
        }),
    )
    
    readonly_fields = ['source_context_display', 'ai_analysis_display', 'status_radio_group']
    
    def severity_badge(self, obj):
        color = obj.severity_color
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, obj.severity
        )
    severity_badge.short_description = '严重程度'
    
    def status_badges(self, obj):
        badges = []
        if obj.verified:
            badges.append('<span style="background-color: #28a745; color: white; padding: 2px 6px; margin: 1px; border-radius: 3px;">已验证</span>')
        if obj.false_p:
            badges.append('<span style="background-color: #ffc107; color: black; padding: 2px 6px; margin: 1px; border-radius: 3px;">误报</span>')
        if obj.is_mitigated:
            badges.append('<span style="background-color: #17a2b8; color: white; padding: 2px 6px; margin: 1px; border-radius: 3px;">已修复</span>')
        if not badges:
            badges.append('<span style="background-color: #dc3545; color: white; padding: 2px 6px; margin: 1px; border-radius: 3px;">活跃</span>')
        return mark_safe(''.join(badges))
    status_badges.short_description = '状态'
    
    def source_context_display(self, obj):
        if not obj.source_context or not obj.source_context.get('lines'):
            return '源码上下文不可用'
        
        lines_text = []
        for line in obj.source_context.get('lines', []):
            line_num = str(line.get('number', '?')).rjust(4)
            content = line.get('content', '')
            marker = '>>> ' if line.get('is_target') else '    '
            lines_text.append(f'{marker}{line_num}: {content}')
        
        return format_html(
            '<pre style="background: #f8f9fa; padding: 15px; border-radius: 4px; font-size: 13px; line-height: 1.4; max-height: 300px; overflow-y: auto;">{}</pre>',
            '\n'.join(lines_text)
        )
    source_context_display.short_description = '源码上下文'
    
    def ai_analysis_display(self, obj):
        if not obj.ai_analysis or not obj.ai_analysis.get('risk_analysis'):
            return format_html(
                '<p>暂无AI分析结果</p>'
                '<button onclick="analyzeWithAI({})" id="ai-btn-{}" style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">开始AI分析</button>'
                '<script>'
                'function analyzeWithAI(id) {'
                '  const btn = document.getElementById("ai-btn-" + id);'
                '  if(btn.disabled) return;'
                '  btn.disabled = true; btn.innerHTML = "分析中...";'
                '  fetch("/finding/" + id + "/ai_analyze/", {'
                '    method: "POST",'
                '    headers: {"X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value}'
                '  })'
                '  .then(r => r.json())'
                '  .then(d => { if(d.success) location.reload(); else { alert("失败"); btn.disabled=false; btn.innerHTML="开始AI分析"; } })'
                '  .catch(() => { btn.disabled=false; btn.innerHTML="开始AI分析"; });'
                '}'
                '</script>',
                obj.id, obj.id
            )
        
        analysis_parts = []
        if obj.ai_analysis.get('risk_analysis'):
            analysis_parts.append(f"安全风险:\n{obj.ai_analysis['risk_analysis']}")
        if obj.ai_analysis.get('solution'):
            analysis_parts.append(f"修复方案:\n{obj.ai_analysis['solution']}")
        if obj.ai_analysis.get('prevention'):
            analysis_parts.append(f"防范建议:\n{obj.ai_analysis['prevention']}")
        
        return format_html(
            '<pre style="background: #f8f9fa; padding: 15px; border-radius: 4px; font-size: 13px; line-height: 1.4; max-height: 400px; overflow-y: auto; white-space: pre-wrap;">{}</pre>',
            '\n\n'.join(analysis_parts)
        )
    ai_analysis_display.short_description = 'AI分析结果'
    
    def status_radio_group(self, obj):
        status_options = [
            ('active', '活跃状态', obj.active),
            ('verified', '已验证', obj.verified),
            ('false_p', '误报', obj.false_p),
            ('duplicate', '重复', obj.duplicate),
            ('out_of_scope', '超出范围', obj.out_of_scope),
            ('risk_accepted', '风险接受', obj.risk_accepted),
            ('under_review', '审核中', obj.under_review),
            ('is_mitigated', '已修复', obj.is_mitigated),
        ]
        
        current_status = 'active'
        for status_key, _, is_selected in status_options:
            if is_selected:
                current_status = status_key
                break
        
        radio_buttons = []
        for status_key, status_label, _ in status_options:
            checked = 'checked' if status_key == current_status else ''
            radio_buttons.append(
                f'<label style="display: block; margin: 5px 0; padding: 8px; border-radius: 4px; background: {"#e3f2fd" if checked else "#f8f9fa"}; border: 1px solid {"#2196f3" if checked else "#dee2e6"}; cursor: pointer;">'
                f'<input type="radio" name="status_group_{obj.id}" value="{status_key}" {checked} '
                f'onchange="updateStatus({obj.id}, \'{status_key}\')" style="margin-right: 8px;">'
                f'<span>{status_label}</span>'
                f'</label>'
            )
        
        return format_html(
            '<div>{}</div>'
            '<script>'
            'function updateStatus(findingId, statusKey) {'
            '  const formData = new FormData();'
            '  formData.append("status_key", statusKey);'
            '  fetch("/finding/" + findingId + "/update_status/", {'
            '    method: "POST", body: formData,'
            '    headers: { "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value }'
            '  })'
            '  .then(response => response.json())'
            '  .then(data => {'
            '    if(data.success) { console.log("状态更新成功"); }'
            '    else { alert("状态更新失败"); location.reload(); }'
            '  })'
            '  .catch(error => { console.error("请求失败"); location.reload(); });'
            '}'
            '</script>',
            ''.join(radio_buttons)
        )
    status_radio_group.short_description = '漏洞状态'


@admin.register(FindingNote)
class FindingNoteAdmin(admin.ModelAdmin):
    list_display = ['finding', 'author', 'content_preview', 'is_private', 'created_at']
    list_filter = ['is_private', 'created_at', 'author']
    search_fields = ['finding__title', 'content', 'author__username']
    ordering = ['-created_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '内容预览'


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['finding', 'from_status', 'to_status', 'changed_by', 'created_at']
    list_filter = ['from_status', 'to_status', 'created_at']
    search_fields = ['finding__title', 'changed_by__username', 'reason']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


admin.site.site_header = '智能代码安全分析平台'
admin.site.site_title = '代码安全分析管理'
admin.site.index_title = '欢迎使用智能代码安全分析平台'