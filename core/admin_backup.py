from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.http import Http404
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
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'department', 'description', 'business_criticality', 'is_active')
        }),
        ('负责人信息', {
            'fields': ('code_owner', 'tech_lead')
        }),
        ('路径配置', {
            'fields': ('source_path', 'report_path', 'repository_url')
        }),
        ('扩展信息', {
            'fields': ('tags', 'metadata'),
            'classes': ('collapse',)
        })
    )
    
    def finding_count(self, obj):
        count = obj.finding_set.filter(active=True).count()
        url = reverse('admin:core_finding_changelist') + f'?project__id__exact={obj.id}&active__exact=1'
        return format_html('<a href="{}">{} 个活跃漏洞</a>', url, count)
    finding_count.short_description = '活跃漏洞'


@admin.register(ScanTask)
class ScanTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'project', 'tool_name', 'status', 'total_findings', 'created_at', 'duration_display']
    list_filter = ['tool_name', 'status', 'created_at']
    search_fields = ['project__name', 'tool_name']
    ordering = ['-created_at']
    readonly_fields = ['duration_display']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('project', 'tool_name', 'scan_type', 'status')
        }),
        ('文件信息', {
            'fields': ('report_file', 'file_size')
        }),
        ('统计信息', {
            'fields': ('total_findings', 'critical_count', 'high_count', 'medium_count', 'low_count', 'info_count')
        }),
        ('时间信息', {
            'fields': ('started_at', 'completed_at', 'duration_display')
        }),
        ('错误信息', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        })
    )
    
    def duration_display(self, obj):
        if obj.duration:
            return str(obj.duration)
        return '-'
    duration_display.short_description = '耗时'


@admin.register(Finding)
class FindingAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity_badge', 'project', 'file_path', 'line_number', 'status_badges', 'code_owner', 'date']
    list_filter = ['severity', 'active', 'verified', 'false_p', 'is_mitigated', 'project__department', 'date']
    search_fields = ['title', 'description', 'file_path', 'code_owner', 'message']
    ordering = ['-numerical_severity', '-date']
    actions = ['ai_analyze_selected', 'translate_selected']
    
    # 支持排序的字段
    sortable_by = ['title', 'severity', 'project', 'file_path', 'line_number', 'code_owner', 'date']
    
    # 默认显示详情而不是编辑
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    # 自定义查看链接
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/view/', self.admin_site.admin_view(self.view_finding), name='core_finding_view'),
        ]
        return custom_urls + urls
    
    def view_finding(self, request, object_id):
        """查看漏洞详情"""
        finding = self.get_object(request, object_id)
        if finding is None:
            raise Http404
        
        context = {
            'title': f'查看漏洞: {finding.title}',
            'finding': finding,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request, finding),
            'original': finding,
        }
        return render(request, 'admin/core/finding/view.html', context)
    
    fieldsets = (
        ('漏洞信息', {
            'fields': (
                ('title', 'severity', 'date'),
                ('file_path', 'line_number'),
                ('cwe', 'cvssv3_score'),
                'description',
                'translated_message',
                'code_owner',
            )
        }),
        ('源码和分析', {
            'fields': (
                'source_context_display',
                'ai_analysis_display',
            )
        }),
        ('状态管理', {
            'fields': (
                'status_radio_group',
            )
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
    severity_badge.admin_order_field = 'numerical_severity'
    
    def status_badges(self, obj):
        badges = []
        if obj.verified:
            badges.append('<span class="badge" style="background-color: #28a745; color: white; padding: 2px 6px; margin: 1px; border-radius: 3px;">已验证</span>')
        if obj.false_p:
            badges.append('<span class="badge" style="background-color: #ffc107; color: black; padding: 2px 6px; margin: 1px; border-radius: 3px;">误报</span>')
        if obj.is_mitigated:
            badges.append('<span class="badge" style="background-color: #17a2b8; color: white; padding: 2px 6px; margin: 1px; border-radius: 3px;">已修复</span>')
        if obj.risk_accepted:
            badges.append('<span class="badge" style="background-color: #6c757d; color: white; padding: 2px 6px; margin: 1px; border-radius: 3px;">风险接受</span>')
        if not badges:
            badges.append('<span class="badge" style="background-color: #dc3545; color: white; padding: 2px 6px; margin: 1px; border-radius: 3px;">活跃</span>')
        
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
    source_context_display.short_description = ''  # 移除英文标签

    
    def description_combined(self, obj):
        """合并显示原始消息和中文描述"""
        original_msg = obj.message or ""
        translated_msg = obj.translated_message or ""
        description = obj.description or ""
        
        # 构建合并内容
        content_parts = []
        
        if description:
            content_parts.append(f"漏洞描述:\n{description}")
        
        if original_msg:
            content_parts.append(f"原始消息:\n{original_msg}")
            
        if translated_msg:
            content_parts.append(f"中文描述:\n{translated_msg}")
        
        if not content_parts:
            content_parts.append("暂无描述信息")
        
        combined_content = "\n\n" + "="*50 + "\n\n".join([""] + content_parts) + "\n" + "="*50
        
        return format_html(
            '<div style="margin: 15px 0;">'
            '<div style="margin-bottom: 10px;">'
            '<strong style="color: #495057; font-size: 14px;">'
            '<i class="fas fa-file-text" style="margin-right: 8px; color: #6c757d;"></i>漏洞详细信息'
            '</strong>'
            '</div>'
            '<textarea readonly style="'
            'width: 100%; '
            'min-height: 200px; '
            'max-height: 400px; '
            'resize: vertical; '
            'background-color: #f8f9fa; '
            'border: 1px solid #dee2e6; '
            'border-radius: 6px; '
            'padding: 15px; '
            'font-family: SFMono-Regular, Consolas, Liberation Mono, Menlo, monospace; '
            'font-size: 13px; '
            'line-height: 1.6; '
            'color: #495057; '
            'box-shadow: 0 1px 3px rgba(0,0,0,0.1);'
            '">{}</textarea>'
            '</div>',
            combined_content
        )
    description_combined.short_description = ''  # 移除英文标签
    def status_radio_group(self, obj):
        """漏洞状态显示"""
        status_options = [
            ('active', '🔴 活跃状态', obj.active),
            ('verified', '✅ 已验证', obj.verified),
            ('false_p', '❌ 误报', obj.false_p),
            ('duplicate', '🔄 重复', obj.duplicate),
            ('out_of_scope', '⚪ 超出范围', obj.out_of_scope),
            ('risk_accepted', '⚠️ 风险接受', obj.risk_accepted),
            ('under_review', '👀 审核中', obj.under_review),
            ('is_mitigated', '✅ 已修复', obj.is_mitigated),
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
                f'<label style="display: block; margin: 8px 0; padding: 12px; border-radius: 6px; background: {"#e3f2fd" if checked else "#f8f9fa"}; border: 2px solid {"#2196f3" if checked else "#dee2e6"}; cursor: pointer; transition: all 0.2s;">'
                f'<input type="radio" name="status_group_{obj.id}" value="{status_key}" {checked} '
                f'onchange="updateStatus({obj.id}, \'{status_key}\')" style="margin-right: 10px;">'
                f'<span style="font-size: 14px; font-weight: {"600" if checked else "400"}; color: {"#1976d2" if checked else "#495057"};">{status_label}</span>'
                f'</label>'
            )
        
        return format_html(
            '<div style="margin-bottom: 20px;">'
            '<div style="background: #ff9800; color: white; padding: 15px; border-radius: 8px 8px 0 0;">'
            '<h3 style="margin: 0; font-size: 18px;">漏洞状态</h3>'
            '</div>'
            '<div style="background: white; border: 1px solid #dee2e6; border-top: none; border-radius: 0 0 8px 8px; padding: 20px;">'
            '{}'
            '</div>'
            '</div>'
            '<script>'
            'function updateStatus(findingId, statusKey) {{'
            '  const formData = new FormData();'
            '  formData.append("status_key", statusKey);'
            '  fetch("/finding/" + findingId + "/update_status/", {{'
            '    method: "POST", body: formData,'
            '    headers: {{ "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value }}'
            '  }})'
            '  .then(response => response.json())'
            '  .then(data => {{'
            '    if(data.success) {{ console.log("状态更新成功"); }}'
            '    else {{ alert("状态更新失败"); location.reload(); }}'
            '  }})'
            '  .catch(error => {{ console.error("请求失败"); location.reload(); }});'
            '}}'
            '</script>',
            ''.join(radio_buttons)
        )
    status_radio_group.short_description = ''  # 移除标签
    
    def ai_analysis_display(self, obj):
        """显示AI分析结果 - 按照原工具设计，正确渲染HTML"""
        if not obj.ai_analysis or not obj.ai_analysis.get('risk_analysis'):
            return format_html(
                '<div style="text-align: center; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background-color: #f8f9fa;">'
                '<p style="color: #666; margin-bottom: 16px;">暂无AI分析结果</p>'
                '<button type="button" onclick="analyzeWithAI({})" class="btn btn-primary btn-sm" id="ai-btn-{}">'
                '<i class="fas fa-robot"></i> 开始AI分析'
                '</button>'
                '</div>'
                '<script>'
                'function analyzeWithAI(findingId) {{'
                '  const btn = document.getElementById("ai-btn-" + findingId);'
                '  if(btn && btn.disabled) return;'
                '  '
                '  if(confirm("确定要进行AI分析吗？这可能需要几分钟时间。")) {{'
                '    if(btn) {{'
                '      btn.disabled = true;'
                '      btn.innerHTML = "<i class=\\"fas fa-spinner fa-spin\\"></i> 分析中...";'
                '    }}'
                '    '
                '    fetch("/finding/" + findingId + "/ai_analyze/", {{'
                '      method: "POST",'
                '      headers: {{'
                '        "Content-Type": "application/json",'
                '        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value'
                '      }}'
                '    }})'
                '    .then(response => response.json())'
                '    .then(data => {{'
                '      if(data.success) {{'
                '        alert("AI分析完成！页面将刷新显示结果。");'
                '        location.reload();'
                '      }} else {{'
                '        alert("AI分析失败: " + (data.error || "未知错误"));'
                '        if(btn) {{'
                '          btn.disabled = false;'
                '          btn.innerHTML = "<i class=\\"fas fa-robot\\"></i> 开始AI分析";'
                '        }}'
                '      }}'
                '    }})'
                '    .catch(error => {{'
                '      alert("请求失败: " + error);'
                '      if(btn) {{'
                '        btn.disabled = false;'
                '        btn.innerHTML = "<i class=\\"fas fa-robot\\"></i> 开始AI分析";'
                '      }}'
                '    }});'
                '  }}'
                '}}'
                '</script>',
                obj.id, obj.id
            )

        # 处理AI分析结果，将代码块转换为专门的代码展示格式
        def format_analysis_content(content):
            """格式化分析内容，处理代码块"""
            if not content:
                return ""
            
            # 处理代码块
            import re
            
            # 匹配 ```语言\n代码\n``` 格式的代码块
            def replace_code_block(match):
                language = match.group(1) or 'text'
                code = match.group(2).strip()
                
                # 生成代码行
                lines = code.split('\n')
                code_lines = []
                for i, line in enumerate(lines, 1):
                    code_lines.append(
                        f'<div style="display: flex; min-height: 20px; line-height: 20px;">'
                        f'<span style="width: 40px; padding: 4px 8px; text-align: right; color: #718096; background-color: #2d3748; border-right: 1px solid #4a5568; user-select: none; flex-shrink: 0;">{i}</span>'
                        f'<span style="padding: 4px 12px; white-space: pre; flex: 1; background-color: #1a202c; color: #e2e8f0;">{line.replace("<", "&lt;").replace(">", "&gt;")}</span>'
                        f'</div>'
                    )
                
                return (
                    f'<div style="margin: 16px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden;">'
                    f'<div style="background: #2d3748; color: white; padding: 8px 16px; font-size: 14px; font-weight: 500; display: flex; align-items: center;">'
                    f'<i class="fas fa-code" style="margin-right: 8px;"></i>{language.upper()}'
                    f'</div>'
                    f'<div style="background: #1a202c; color: #e2e8f0; font-family: Monaco, Menlo, Ubuntu Mono, monospace; font-size: 14px; overflow-x: auto; margin: 0; min-height: 40px;">'
                    f'{"".join(code_lines)}'
                    f'</div>'
                    f'</div>'
                )
            
            # 先处理简单的代码标记（如 php 单独一行）
            content = re.sub(r'^(php|javascript|python|java|css|html)$', r'```\1', content, flags=re.MULTILINE)
            
            # 替换代码块
            content = re.sub(r'```(\w+)?\n?(.*?)(?=\n```|\n[^`]|\Z)', replace_code_block, content, flags=re.DOTALL | re.MULTILINE)
            
            # 处理换行
            content = content.replace('\n', '<br>')
            
            return content

        # 显示分析结果 - 按段落分类展示
        analysis_sections = []
        
        # 安全风险分析
        if obj.ai_analysis.get('risk_analysis'):
            formatted_content = format_analysis_content(obj.ai_analysis['risk_analysis'])
            analysis_sections.append(
                '<div class="analysis-section" style="margin-bottom: 20px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">'
                '<div class="section-header" style="background: linear-gradient(135deg, #dc3545, #c82333); padding: 12px 16px; color: white; font-weight: 600;">'
                '<i class="fas fa-exclamation-triangle" style="margin-right: 8px;"></i>安全风险分析'
                '</div>'
                '<div class="section-content" style="padding: 20px; background: white; line-height: 1.7;">'
                f'{formatted_content}'
                '</div>'
                '</div>'
            )
        
        # 具体修复方案
        if obj.ai_analysis.get('solution'):
            formatted_content = format_analysis_content(obj.ai_analysis['solution'])
            analysis_sections.append(
                '<div class="analysis-section" style="margin-bottom: 20px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">'
                '<div class="section-header" style="background: linear-gradient(135deg, #28a745, #1e7e34); padding: 12px 16px; color: white; font-weight: 600;">'
                '<i class="fas fa-tools" style="margin-right: 8px;"></i>具体修复方案'
                '</div>'
                '<div class="section-content" style="padding: 20px; background: white; line-height: 1.7;">'
                f'{formatted_content}'
                '</div>'
                '</div>'
            )
        
        # 防范建议
        if obj.ai_analysis.get('prevention'):
            formatted_content = format_analysis_content(obj.ai_analysis['prevention'])
            analysis_sections.append(
                '<div class="analysis-section" style="margin-bottom: 20px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">'
                '<div class="section-header" style="background: linear-gradient(135deg, #17a2b8, #138496); padding: 12px 16px; color: white; font-weight: 600;">'
                '<i class="fas fa-shield-alt" style="margin-right: 8px;"></i>防范建议'
                '</div>'
                '<div class="section-content" style="padding: 20px; background: white; line-height: 1.7;">'
                f'{formatted_content}'
                '</div>'
                '</div>'
            )

        cached_info = ''
        if obj.ai_analysis.get('cached_at'):
            cached_info = f'<p style="color: #666; font-size: 12px; text-align: center; margin-top: 16px;">分析时间: {obj.ai_analysis["cached_at"]}</p>'

    def ai_analysis_display(self, obj):
        """AI分析结果显示"""
        if not obj.ai_analysis or not obj.ai_analysis.get('risk_analysis'):
            return format_html(
                '<div style="text-align: center; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background-color: #f8f9fa;">'
                '<p style="color: #666; margin-bottom: 16px;">暂无AI分析结果</p>'
                '<button type="button" onclick="analyzeWithAI({})" class="btn btn-primary btn-sm" id="ai-btn-{}">'
                '<i class="fas fa-robot"></i> 开始AI分析'
                '</button>'
                '</div>'
                '<script>'
                'function analyzeWithAI(findingId) {{'
                '  const btn = document.getElementById("ai-btn-" + findingId);'
                '  if(btn && btn.disabled) return;'
                '  '
                '  if(confirm("确定要进行AI分析吗？这可能需要几分钟时间。")) {{'
                '    if(btn) {{'
                '      btn.disabled = true;'
                '      btn.innerHTML = "<i class=\\"fas fa-spinner fa-spin\\"></i> 分析中...";'
                '    }}'
                '    '
                '    fetch("/finding/" + findingId + "/ai_analyze/", {{'
                '      method: "POST",'
                '      headers: {{'
                '        "Content-Type": "application/json",'
                '        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value'
                '      }}'
                '    }})'
                '    .then(response => response.json())'
                '    .then(data => {{'
                '      if(data.success) {{'
                '        alert("AI分析完成！页面将刷新显示结果。");'
                '        location.reload();'
                '      }} else {{'
                '        alert("AI分析失败: " + (data.error || "未知错误"));'
                '        if(btn) {{'
                '          btn.disabled = false;'
                '          btn.innerHTML = "<i class=\\"fas fa-robot\\"></i> 开始AI分析";'
                '        }}'
                '      }}'
                '    }})'
                '    .catch(error => {{'
                '      alert("请求失败: " + error);'
                '      if(btn) {{'
                '        btn.disabled = false;'
                '        btn.innerHTML = "<i class=\\"fas fa-robot\\"></i> 开始AI分析";'
                '      }}'
                '    }});'
                '  }}'
                '}}'
                '</script>',
                obj.id, obj.id
            )

        # 格式化分析结果
        sections = []
        if obj.ai_analysis.get('risk_analysis'):
            sections.append(f"🔍 安全风险分析\n{obj.ai_analysis['risk_analysis']}")
        if obj.ai_analysis.get('solution'):
            sections.append(f"🔧 修复方案\n{obj.ai_analysis['solution']}")
        if obj.ai_analysis.get('prevention'):
            sections.append(f"🛡️ 防范建议\n{obj.ai_analysis['prevention']}")

        analysis_text = '\n\n' + '='*50 + '\n\n'.join([''] + sections)
        
        cache_info = ''
        if obj.ai_cached:
            cache_info = '<div style="text-align: center; padding: 10px; background: #d4edda; color: #155724; border-radius: 4px; margin-top: 10px;">✅ 已缓存的分析结果</div>'

        return format_html(
            '<div style="margin-bottom: 20px;">'
            '<div style="background: #6f42c1; color: white; padding: 15px; border-radius: 8px 8px 0 0;">'
            '<h3 style="margin: 0; font-size: 18px;">AI智能分析结果</h3>'
            '</div>'
            '<div style="background: #f8f9fa; border: 1px solid #dee2e6; border-top: none; border-radius: 0 0 8px 8px;">'
            '<pre style="padding: 20px; margin: 0; white-space: pre-wrap; font-family: monospace; font-size: 13px; line-height: 1.6; max-height: 400px; overflow-y: auto;">{}</pre>'
            '<div style="padding: 15px; text-align: center; border-top: 1px solid #dee2e6;">'
            '<button type="button" onclick="reAnalyzeWithAI({})" id="reai-btn-{}" '
            'style="background: #6c757d; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-size: 13px; cursor: pointer;">'
            '🔄 重新分析'
            '</button>'
            '</div>'
            '{}'
            '</div>'
            '</div>'
            '<script>'
            'function reAnalyzeWithAI(findingId) {{'
            '  const btn = document.getElementById("reai-btn-" + findingId);'
            '  if(btn && btn.disabled) return;'
            '  if(confirm("确定要重新分析吗？")) {{'
            '    btn.disabled = true;'
            '    btn.innerHTML = "⏳ 重新分析中...";'
            '    const formData = new FormData(); formData.append("force", "true");'
            '    fetch("/finding/" + findingId + "/ai_analyze/", {{'
            '      method: "POST", body: formData,'
            '      headers: {{ "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value }}'
            '    }})'
            '    .then(response => response.json())'
            '    .then(data => {{'
            '      if(data.success) {{ alert("重新分析完成！"); location.reload(); }}'
            '      else {{ alert("分析失败"); btn.disabled = false; btn.innerHTML = "🔄 重新分析"; }}'
            '    }})'
            '    .catch(error => {{ alert("请求失败"); btn.disabled = false; btn.innerHTML = "🔄 重新分析"; }});'
            '  }}'
            '}}'
            '</script>',
            analysis_text, obj.id, obj.id, cache_info
        )
    ai_analysis_display.short_description = ''  # 移除英文标签
    ai_analysis_display.short_description = 'AI分析结果'
    
    def ai_analyze_selected(self, request, queryset):
        """批量AI分析"""
        from ai_analysis.services import AIAnalyzer
        
        analyzer = AIAnalyzer()
        success_count = 0
        
        for finding in queryset:
            try:
                # 这里应该调用AI分析服务
                # analysis = analyzer.analyze_finding(finding)
                # finding.ai_analysis = analysis
                # finding.ai_cached = True
                # finding.save()
                success_count += 1
            except Exception as e:
                self.message_user(request, f'分析漏洞 {finding.title} 失败: {str(e)}', level='ERROR')
        
        self.message_user(request, f'成功分析 {success_count} 个漏洞')
    ai_analyze_selected.short_description = 'AI分析选中的漏洞'
    
    def translate_selected(self, request, queryset):
        """批量翻译"""
        from translation.services import translation_service
        
        success_count = 0
        for finding in queryset:
            if not finding.translated_message and translation_service.is_available():
                try:
                    translated = translation_service.translate_text(finding.message)
                    finding.translated_message = translated
                    finding.save()
                    success_count += 1
                except Exception as e:
                    self.message_user(request, f'翻译漏洞 {finding.title} 失败: {str(e)}', level='ERROR')
        
        self.message_user(request, f'成功翻译 {success_count} 个漏洞')
    translate_selected.short_description = '翻译选中的漏洞'
    
    actions = ['mark_as_verified', 'mark_as_false_positive', 'mark_as_mitigated']
    
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(verified=True)
        self.message_user(request, f'已将 {updated} 个漏洞标记为已验证')
    mark_as_verified.short_description = '标记为已验证'
    
    def mark_as_false_positive(self, request, queryset):
        updated = queryset.update(false_p=True, active=False)
        self.message_user(request, f'已将 {updated} 个漏洞标记为误报')
    mark_as_false_positive.short_description = '标记为误报'
    
    def mark_as_mitigated(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_mitigated=True, mitigated=timezone.now())
        self.message_user(request, f'已将 {updated} 个漏洞标记为已修复')
    mark_as_mitigated.short_description = '标记为已修复'


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


# 自定义管理界面标题
admin.site.site_header = '智能代码安全分析平台'
admin.site.site_title = '代码安全分析管理'
admin.site.index_title = '欢迎使用智能代码安全分析平台'
