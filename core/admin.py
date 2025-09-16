from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Q
from .models import Department, Project, ScanTask, Finding, FindingNote, StatusHistory
import subprocess
import logging
import os

logger = logging.getLogger(__name__)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'lead', 'project_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description', 'lead']
    ordering = ['name']
    
    def render_change_form(self, request, context, *args, **kwargs):
        context['back_script'] = mark_safe('<script>document.addEventListener("DOMContentLoaded", function() { const h1 = document.querySelector("h1"); if (h1) { const btn = document.createElement("button"); btn.innerHTML = "← 返回"; btn.style.cssText = "margin-left: 15px; padding: 6px 12px; background: #6c757d; color: white; border: none; border-radius: 4px; font-size: 13px; cursor: pointer;"; btn.onclick = function() { history.back(); }; h1.appendChild(btn); } });</script>')
        return super().render_change_form(request, context, *args, **kwargs)
    
    def project_count(self, obj):
        count = obj.project_set.count()
        url = reverse('admin:core_project_changelist') + f'?department__id__exact={obj.id}'
        return format_html('<a href="{}">{} 个项目</a>', url, count)
    project_count.short_description = '项目数量'
    
    def save_model(self, request, obj, form, change):
        """保存部门时创建目录结构"""
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        
        if is_new:
            try:
                from django.conf import settings
                
                # 创建部门目录
                dept_project_dir = os.path.join(settings.AUTO_SCAN_CONFIG['PROJECT_DIR'], obj.name)
                dept_report_dir = os.path.join(settings.AUTO_SCAN_CONFIG['OUTPUT_DIR'], obj.name)
                
                os.makedirs(dept_project_dir, exist_ok=True)
                os.makedirs(dept_report_dir, exist_ok=True)
                
                logger.info(f"已为部门 {obj.name} 创建目录结构")
                
            except Exception as e:
                logger.error(f"创建部门目录失败: {e}")
    
    def delete_model(self, request, obj):
        """删除部门时清理所有相关数据"""
        try:
            from django.conf import settings
            
            # 1. 先删除所有相关项目（会自动清理漏洞和任务）
            projects = Project.objects.filter(department=obj)
            project_count = projects.count()
            
            for project in projects:
                # 终止运行中的扫描任务
                running_tasks = ScanTask.objects.filter(project=project, status='running')
                for task in running_tasks:
                    try:
                        project_path = os.path.join(settings.AUTO_SCAN_CONFIG['PROJECT_DIR'], obj.name, project.name)
                        subprocess.run(f"pkill -9 -f '{project_path}' 2>/dev/null || true", shell=True)
                        subprocess.run(f"pkill -9 -f 'scan_{project.id}' 2>/dev/null || true", shell=True)
                        
                        task.status = 'failed'
                        task.error_message = '部门已删除，扫描任务已终止'
                        task.save()
                    except Exception as e:
                        logger.error(f"终止扫描任务失败: {e}")
            
            # 2. 删除所有相关数据
            finding_count = Finding.objects.filter(project__department=obj).count()
            task_count = ScanTask.objects.filter(project__department=obj).count()
            
            Finding.objects.filter(project__department=obj).delete()
            ScanTask.objects.filter(project__department=obj).delete()
            projects.delete()
            
            # 3. 清理部门目录
            dept_project_dir = os.path.join(settings.AUTO_SCAN_CONFIG['PROJECT_DIR'], obj.name)
            dept_report_dir = os.path.join(settings.AUTO_SCAN_CONFIG['OUTPUT_DIR'], obj.name)
            
            subprocess.run(f"rm -rf '{dept_project_dir}' 2>/dev/null || true", shell=True)
            subprocess.run(f"rm -rf '{dept_report_dir}' 2>/dev/null || true", shell=True)
            
            logger.info(f"已删除部门 {obj.name}，清理了 {project_count} 个项目、{finding_count} 个漏洞和 {task_count} 个扫描任务")
            
        except Exception as e:
            logger.error(f"删除部门时清理失败: {e}")
        
        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        """批量删除部门时清理所有相关数据"""
        for obj in queryset:
            self.delete_model(request, obj)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'code_owner', 'business_criticality', 'finding_count', 'is_active', 'created_at']
    list_filter = ['department', 'business_criticality', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'code_owner', 'tech_lead']
    ordering = ['department__name', 'name']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'department', 'description', 'code_owner', 'business_criticality', 'is_active')
        }),
        ('代码仓库', {
            'fields': ('repository_url', 'build_command')
        }),
    )
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['back_script'] = mark_safe('<script>document.addEventListener("DOMContentLoaded", function() { const h1 = document.querySelector("h1"); if (h1) { const btn = document.createElement("button"); btn.innerHTML = "← 返回"; btn.style.cssText = "margin-left: 15px; padding: 6px 12px; background: #6c757d; color: white; border: none; border-radius: 4px; font-size: 13px; cursor: pointer;"; btn.onclick = function() { history.back(); }; h1.appendChild(btn); } });</script>')
        return super().changelist_view(request, extra_context)
    
    def render_change_form(self, request, context, *args, **kwargs):
        context['back_script'] = mark_safe('<script>document.addEventListener("DOMContentLoaded", function() { const h1 = document.querySelector("h1"); if (h1) { const btn = document.createElement("button"); btn.innerHTML = "← 返回"; btn.style.cssText = "margin-left: 15px; padding: 6px 12px; background: #6c757d; color: white; border: none; border-radius: 4px; font-size: 13px; cursor: pointer;"; btn.onclick = function() { history.back(); }; h1.appendChild(btn); } });</script>')
        return super().render_change_form(request, context, *args, **kwargs)
    
    def finding_count(self, obj):
        count = obj.finding_set.filter(active=True).count()
        url = reverse('admin:core_finding_changelist') + f'?project__id__exact={obj.id}&active__exact=1'
        return format_html('<a href="{}">{} 个活跃漏洞</a>', url, count)
    finding_count.short_description = '活跃漏洞'
    
    def save_model(self, request, obj, form, change):
        """保存项目时创建目录结构"""
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        
        if is_new:
            # 新项目，创建目录结构
            try:
                from django.conf import settings
                import os
                
                # 创建项目源码目录
                project_dir = os.path.join(settings.AUTO_SCAN_CONFIG['PROJECT_DIR'], obj.department.name, obj.name)
                os.makedirs(project_dir, exist_ok=True)
                
                # 创建项目报告目录
                report_dir = os.path.join(settings.AUTO_SCAN_CONFIG['OUTPUT_DIR'], obj.department.name, obj.name)
                os.makedirs(report_dir, exist_ok=True)
                
                logger.info(f"已为项目 {obj.department.name}/{obj.name} 创建目录结构")
                
            except Exception as e:
                logger.error(f"创建项目目录失败: {e}")
    
    def delete_model(self, request, obj):
        """删除项目时清理所有相关数据"""
        try:
            from django.conf import settings
            import os
            
            # 1. 终止运行中的扫描任务
            running_tasks = ScanTask.objects.filter(project=obj, status='running')
            for task in running_tasks:
                try:
                    project_path = os.path.join(settings.AUTO_SCAN_CONFIG['PROJECT_DIR'], obj.department.name, obj.name)
                    subprocess.run(f"pkill -9 -f '{project_path}' 2>/dev/null || true", shell=True)
                    subprocess.run(f"pkill -9 -f 'scan_{obj.id}' 2>/dev/null || true", shell=True)
                    
                    task.status = 'failed'
                    task.error_message = '项目已删除，扫描任务已终止'
                    task.save()
                    
                except Exception as e:
                    logger.error(f"终止扫描任务失败: {e}")
            
            # 2. 删除所有相关的漏洞记录
            finding_count = Finding.objects.filter(project=obj).count()
            Finding.objects.filter(project=obj).delete()
            
            # 3. 删除所有相关的扫描任务
            task_count = ScanTask.objects.filter(project=obj).count()
            ScanTask.objects.filter(project=obj).delete()
            
            # 4. 清理项目目录
            project_dir = os.path.join(settings.AUTO_SCAN_CONFIG['PROJECT_DIR'], obj.department.name, obj.name)
            report_dir = os.path.join(settings.AUTO_SCAN_CONFIG['OUTPUT_DIR'], obj.department.name, obj.name)
            
            subprocess.run(f"rm -rf '{project_dir}' 2>/dev/null || true", shell=True)
            subprocess.run(f"rm -rf '{report_dir}' 2>/dev/null || true", shell=True)
            
            # 5. 清理临时文件
            temp_dir = os.path.join(settings.AUTO_SCAN_CONFIG['WORK_DIR'], f'scan_{obj.id}')
            subprocess.run(f"rm -rf '{temp_dir}' 2>/dev/null || true", shell=True)
            
            logger.info(f"已删除项目 {obj.name}，清理了 {finding_count} 个漏洞和 {task_count} 个扫描任务")
            
        except Exception as e:
            logger.error(f"删除项目时清理失败: {e}")
        
        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        """批量删除项目时清理所有相关数据"""
        for obj in queryset:
            self.delete_model(request, obj)


@admin.register(ScanTask)
class ScanTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'project', 'tool_name', 'status', 'total_findings', 'created_at']
    list_filter = ['tool_name', 'status', 'created_at']
    search_fields = ['project__name', 'tool_name']
    ordering = ['-created_at']
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['back_script'] = mark_safe('<script>document.addEventListener("DOMContentLoaded", function() { const h1 = document.querySelector("h1"); if (h1) { const btn = document.createElement("button"); btn.innerHTML = "← 返回"; btn.style.cssText = "margin-left: 15px; padding: 6px 12px; background: #6c757d; color: white; border: none; border-radius: 4px; font-size: 13px; cursor: pointer;"; btn.onclick = function() { history.back(); }; h1.appendChild(btn); } });</script>')
        return super().changelist_view(request, extra_context)
    
    def add_view(self, request, form_url='', extra_context=None):
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect('/api/quick-scan/')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        for field in form.base_fields.values():
            field.required = False
        return form
    
    def render_change_form(self, request, context, *args, **kwargs):
        context['back_script'] = mark_safe('<script>document.addEventListener("DOMContentLoaded", function() { const h1 = document.querySelector("h1"); if (h1) { const btn = document.createElement("button"); btn.innerHTML = "← 返回"; btn.style.cssText = "margin-left: 15px; padding: 6px 12px; background: #6c757d; color: white; border: none; border-radius: 4px; font-size: 13px; cursor: pointer;"; btn.onclick = function() { history.back(); }; h1.appendChild(btn); } });</script>')
        return super().render_change_form(request, context, *args, **kwargs)


@admin.register(Finding)
class FindingAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity_badge', 'project', 'file_path', 'line_number', 'status_badges', 'ai_quality_badge', 'code_owner', 'date']
    list_filter = ['severity', 'active', 'verified', 'false_p', 'is_mitigated', 'ai_quality_rating', 'project__department', 'date']
    search_fields = ['title', 'description', 'file_path', 'code_owner', 'message']
    ordering = ['-numerical_severity', '-date']
    sortable_by = ['title', 'severity_badge', 'project', 'file_path', 'line_number', 'status_badges', 'code_owner', 'date']
    actions = ['mark_as_verified', 'mark_as_false_positive', 'mark_as_mitigated', 'reactivate_findings', 'batch_ai_analyze']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'severity', 'date', 'file_location_display', 'cwe', 'cvssv3_score', 'description_combined')
        }),
        ('源码和分析', {
            'fields': ('source_context_display', 'ai_analysis_display')
        }),
        ('状态管理', {
            'fields': ('status_radio_group',)
        }),
        ('负责人', {
            'fields': ('code_owner',)
        }),
        ('AI质量评估', {
            'fields': ('ai_quality_display',)
        }),
    )
    
    readonly_fields = ['file_location_display', 'description_combined', 'source_context_display', 'ai_analysis_display', 'status_radio_group', 'ai_quality_display']
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['back_script'] = mark_safe('<script>document.addEventListener("DOMContentLoaded", function() { const h1 = document.querySelector("h1"); if (h1) { const btn = document.createElement("button"); btn.innerHTML = "← 返回"; btn.style.cssText = "margin-left: 15px; padding: 6px 12px; background: #6c757d; color: white; border: none; border-radius: 4px; font-size: 13px; cursor: pointer;"; btn.onclick = function() { history.back(); }; h1.appendChild(btn); } });</script>')
        return super().changelist_view(request, extra_context)
    
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
            badges.append('<span style="background-color: #28a745; color: white; padding: 2px 6px; margin: 1px; border-radius: 3px;">已验证</span>')
        if obj.false_p:
            badges.append('<span style="background-color: #ffc107; color: black; padding: 2px 6px; margin: 1px; border-radius: 3px;">误报</span>')
        if obj.is_mitigated:
            badges.append('<span style="background-color: #17a2b8; color: white; padding: 2px 6px; margin: 1px; border-radius: 3px;">已修复</span>')
        if not badges:
            badges.append('<span style="background-color: #dc3545; color: white; padding: 2px 6px; margin: 1px; border-radius: 3px;">活跃</span>')
        return mark_safe(''.join(badges))
    status_badges.short_description = '状态'
    status_badges.admin_order_field = 'active'
    
    def ai_quality_badge(self, obj):
        """AI质量评估徽章"""
        if not obj.ai_quality_rating:
            return format_html('<span style="color: #6c757d;">未评估</span>')
        
        colors = {
            'excellent': '#28a745',  # 绿色
            'good': '#ffc107',       # 黄色
            'poor': '#dc3545'        # 红色
        }
        
        labels = {
            'excellent': '优秀',
            'good': '良好', 
            'poor': '差'
        }
        
        color = colors.get(obj.ai_quality_rating, '#6c757d')
        label = labels.get(obj.ai_quality_rating, obj.ai_quality_rating)
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, label
        )
    ai_quality_badge.short_description = 'AI质量'
    ai_quality_badge.admin_order_field = 'ai_quality_rating'
    
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(verified=True, active=False)
        self.message_user(request, f'已将 {updated} 个漏洞标记为已验证')
    mark_as_verified.short_description = '标记为已验证'
    
    def mark_as_false_positive(self, request, queryset):
        updated = queryset.update(false_p=True, active=False)
        self.message_user(request, f'已将 {updated} 个漏洞标记为误报')
    mark_as_false_positive.short_description = '标记为误报'
    
    def mark_as_mitigated(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_mitigated=True, mitigated=timezone.now(), active=False)
        self.message_user(request, f'已将 {updated} 个漏洞标记为已修复')
    mark_as_mitigated.short_description = '标记为已修复'
    
    def reactivate_findings(self, request, queryset):
        updated = queryset.update(active=True, verified=False, false_p=False, is_mitigated=False, risk_accepted=False, duplicate=False, out_of_scope=False, under_review=False)
        self.message_user(request, f'已重新激活 {updated} 个漏洞')
    reactivate_findings.short_description = '重新激活'
    
    def batch_ai_analyze(self, request, queryset):
        # 过滤出未在分析中且无分析结果的漏洞
        analyzable = queryset.filter(ai_analyzing=False).filter(
            Q(ai_analysis__isnull=True) | 
            Q(ai_analysis__risk_analysis__isnull=True) |
            Q(ai_analysis__risk_analysis='')
        )
        
        # 检查全局并发限制
        current_analyzing = Finding.objects.filter(ai_analyzing=True).count()
        max_concurrent = 10
        available_slots = max_concurrent - current_analyzing
        
        if available_slots <= 0:
            self.message_user(request, f'当前有{current_analyzing}个AI分析任务正在进行，请稍后再试', level='warning')
            return
        
        # 限制初始启动数量，但允许后续排队
        to_analyze = analyzable
        initial_batch = min(len(to_analyze), available_slots)
        
        if not to_analyze:
            self.message_user(request, '所选漏洞都已有分析结果或正在分析中', level='warning')
            return
        
        # 立即启动可用槽位数量的任务
        initial_findings = list(to_analyze[:initial_batch])
        Finding.objects.filter(id__in=[f.id for f in initial_findings]).update(ai_analyzing=True)
        updated = len(to_analyze)
        
        # 异步启动分析（这里简化为同步，实际可用Celery等）
        from django.http import JsonResponse
        import threading
        
        def analyze_findings():
            for finding in to_analyze:
                # 等待直到有空闲槽位
                while True:
                    current_analyzing = Finding.objects.filter(ai_analyzing=True).count()
                    if current_analyzing < max_concurrent:
                        break
                    import time
                    time.sleep(5)  # 等待5秒再检查
                
                # 重新检查该漏洞状态，防止重复分析
                finding.refresh_from_db()
                if finding.ai_analyzing:
                    continue  # 已在分析中，跳过
                if finding.ai_analysis and finding.ai_analysis.get('risk_analysis'):
                    continue  # 已有分析结果，跳过
                
                # 设置分析状态
                finding.ai_analyzing = True
                finding.save(update_fields=['ai_analyzing'])
                
                try:
                    from .views import _analyze_single_finding, _parse_ai_analysis
                    from datetime import datetime
                    
                    analysis_result = _analyze_single_finding(finding)
                    if analysis_result and not analysis_result.startswith('分析失败'):
                        parsed_analysis = _parse_ai_analysis(analysis_result)
                        parsed_analysis['cached_at'] = datetime.now().isoformat()
                        
                        finding.ai_analysis = parsed_analysis
                        finding.ai_cached = True
                    
                    finding.ai_analyzing = False
                    finding.save(update_fields=['ai_analysis', 'ai_cached', 'ai_analyzing'])
                except Exception as e:
                    finding.ai_analyzing = False
                    finding.save(update_fields=['ai_analyzing'])
        
        # 启动后台分析
        thread = threading.Thread(target=analyze_findings)
        thread.daemon = True
        thread.start()
        
        self.message_user(request, f'已启动 {updated} 个漏洞的AI分析任务')
    batch_ai_analyze.short_description = '批量AI分析'
    

    
    def file_location_display(self, obj):
        return f"{obj.file_path}:{obj.line_number}" if obj.file_path and obj.line_number else (obj.file_path or '未知')
    file_location_display.short_description = '文件位置'
    
    def description_combined(self, obj):
        parts = []
        if obj.description:
            parts.append(obj.description)
        if obj.translated_message:
            parts.append(f"中文描述: {obj.translated_message}")
        elif obj.message:
            parts.append(f"原始描述: {obj.message}")
        
        content = '\n\n'.join(parts) if parts else '暂无描述'
        return format_html(
            '<textarea readonly style="width: 100%; min-width: 600px; height: 150px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; background: #f9f9f9; font-size: 13px; line-height: 1.4; resize: both;">{}</textarea>',
            content
        )
    description_combined.short_description = '漏洞描述'
    
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
        # 检查源代码是否过长
        has_long_lines = False
        if obj.source_context and obj.source_context.get('lines'):
            for line in obj.source_context['lines']:
                if len(line.get('content', '')) > 300:
                    has_long_lines = True
                    break
        
        # 构建长代码警告
        long_code_warning = ''
        if has_long_lines:
            long_code_warning = '<div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 8px; margin-bottom: 10px; border-radius: 4px; color: #856404;">⚠️ 注意：源代码存在超长行，AI分析有截取，分析结果可能不准。</div>'
        
        if obj.ai_analyzing:
            # 正在分析中
            html = long_code_warning + f'<p>AI分析进行中...</p>' + \
                   f'<button onclick="killAIAnalysis({obj.id})" style="padding: 8px 16px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px;">终止分析</button>' + \
                   f'<button disabled style="padding: 8px 16px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: not-allowed;">分析中...</button>' + \
                   '<script>' + \
                   f'function killAIAnalysis(id) {{' + \
                   '  if(confirm("确定要终止AI分析吗？")) {' + \
                   '    fetch("/finding/" + id + "/kill_ai_analyze/", {' + \
                   '      method: "POST",' + \
                   '      headers: {"X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value}' + \
                   '    })' + \
                   '    .then(() => location.reload());' + \
                   '  }' + \
                   '}' + \
                   '</script>'
        elif not obj.ai_analysis or not any(obj.ai_analysis.get(k) for k in ['risk_analysis', 'solution', 'prevention']):
            # 没有分析结果
            html = long_code_warning + f'<p>暂无AI分析结果</p>' + \
                   f'<button onclick="analyzeWithAI({obj.id})" id="ai-btn-{obj.id}" style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">开始AI分析</button>' + \
                   '<script>' + \
                   f'function analyzeWithAI(id) {{' + \
                   '  const btn = document.getElementById("ai-btn-" + id);' + \
                   '  if(btn.disabled) return;' + \
                   '  btn.disabled = true; btn.innerHTML = "分析中...";' + \
                   '  fetch("/finding/" + id + "/ai_analyze/", {' + \
                   '    method: "POST",' + \
                   '    headers: {"X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value}' + \
                   '  })' + \
                   '  .then(r => r.json())' + \
                   '  .then(d => { if(d.success) location.reload(); else { alert(d.error || "失败"); btn.disabled=false; btn.innerHTML="开始AI分析"; } })' + \
                   '  .catch(() => { btn.disabled=false; btn.innerHTML="开始AI分析"; });' + \
                   '}' + \
                   '</script>'
        else:
            # 有分析结果
            analysis_parts = []
            if obj.ai_analysis.get('risk_analysis'):
                analysis_parts.append(f"安全风险：\n{obj.ai_analysis['risk_analysis']}")
            if obj.ai_analysis.get('solution'):
                analysis_parts.append(f"修复方案：\n{obj.ai_analysis['solution']}")
            if obj.ai_analysis.get('prevention'):
                analysis_parts.append(f"防范建议：\n{obj.ai_analysis['prevention']}")
            
            html = long_code_warning + format_html(
                '<pre style="background: #f8f9fa; padding: 15px; border-radius: 4px; font-size: 13px; line-height: 1.4; max-height: 400px; overflow-y: auto; white-space: pre-wrap;">{}</pre>',
                '\n\n'.join(analysis_parts)
            )
        
        return mark_safe(html)
    ai_analysis_display.short_description = 'AI分析结果'
    
    def ai_quality_display(self, obj):
        """AI质量评估显示和输入"""
        labels = {
            'excellent': '完整正确，可以直接用',
            'good': '建议正确，但是不能直接用',
            'poor': '建议错误'
        }
        
        colors = {
            'excellent': '#28a745',
            'good': '#ffc107', 
            'poor': '#dc3545'
        }
        
        html_content = []
        
        # 显示当前评估状态
        if obj.ai_quality_rating:
            rating_label = labels.get(obj.ai_quality_rating, obj.ai_quality_rating)
            rating_color = colors.get(obj.ai_quality_rating, '#6c757d')
            
            current_status = f'''
            <div style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                <div style="margin-bottom: 8px;">
                    <strong>当前评估：</strong> 
                    <span style="background-color: {rating_color}; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold;">{rating_label}</span>
                </div>
            '''
            
            if obj.ai_quality_comment:
                current_status += f'<div style="margin-bottom: 8px;"><strong>评估备注：</strong> {obj.ai_quality_comment}</div>'
            
            if obj.ai_rated_by:
                rated_time = obj.ai_rated_at.strftime("%Y-%m-%d %H:%M:%S") if obj.ai_rated_at else "未知"
                current_status += f'''
                <div style="font-size: 12px; color: #6c757d;">
                    评估人：{obj.ai_rated_by.username} | 评估时间：{rated_time}
                </div>
                '''
            
            current_status += '</div>'
            html_content.append(current_status)
        else:
            html_content.append('<div style="margin-bottom: 15px; color: #6c757d;">暂未评估</div>')
        
        # 添加评估表单 - 横向布局，通过 Django Admin 保存
        form_html = f'''
        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 4px; background: white;">
            <h4 style="margin-bottom: 15px; color: #333;">分析建议准确性勾选</h4>
            <div style="display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap;">
                <label style="cursor: pointer; display: flex; align-items: center; padding: 8px 12px; border: 1px solid #e9ecef; border-radius: 4px; background: #f8f9fa; min-width: 200px;">
                    <input type="radio" name="ai_quality_rating" value="excellent" {'checked' if obj.ai_quality_rating == 'excellent' else ''} style="margin-right: 8px; transform: scale(1.1);">
                    <span style="color: #28a745; font-weight: bold; font-size: 13px;">✓ 1. 完整正确，可以直接用</span>
                </label>
                <label style="cursor: pointer; display: flex; align-items: center; padding: 8px 12px; border: 1px solid #e9ecef; border-radius: 4px; background: #f8f9fa; min-width: 220px;">
                    <input type="radio" name="ai_quality_rating" value="good" {'checked' if obj.ai_quality_rating == 'good' else ''} style="margin-right: 8px; transform: scale(1.1);">
                    <span style="color: #ffc107; font-weight: bold; font-size: 13px;">✓ 2. 建议正确，但是不能直接用</span>
                </label>
                <label style="cursor: pointer; display: flex; align-items: center; padding: 8px 12px; border: 1px solid #e9ecef; border-radius: 4px; background: #f8f9fa; min-width: 140px;">
                    <input type="radio" name="ai_quality_rating" value="poor" {'checked' if obj.ai_quality_rating == 'poor' else ''} style="margin-right: 8px; transform: scale(1.1);">
                    <span style="color: #dc3545; font-weight: bold; font-size: 13px;">✓ 3. 建议错误</span>
                </label>
            </div>
            <div style="margin-bottom: 10px;">
                <label style="display: block; margin-bottom: 8px; font-weight: bold; color: #666;">补充说明（可选）：</label>
                <textarea name="ai_quality_comment" placeholder="如有特殊情况可在此补充说明..." style="width: 100%; height: 50px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; resize: vertical; font-size: 13px;">{obj.ai_quality_comment or ''}</textarea>
            </div>
            <div style="font-size: 12px; color: #6c757d; font-style: italic;">
                提示：选择评估等级后，点击页面底部的"保存"按钮即可提交评估
            </div>
        </div>
        '''
        
        html_content.append(form_html)
        
        return mark_safe(''.join(html_content))
    ai_quality_display.short_description = 'AI质量评估'
    
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
        
        radios = []
        for status_key, status_label, _ in status_options:
            checked = 'checked' if status_key == current_status else ''
            radios.append(
                f'<label style="display: inline-block; margin: 5px 10px; cursor: pointer;">'
                f'<input type="radio" name="status_{obj.id}" value="{status_key}" {checked} '
                f'onchange="updateStatus({obj.id}, \'{status_key}\')" style="margin-right: 5px;">'
                f'{status_label}</label>'
            )
        
        html = f'<div style="padding: 10px;">{"".join(radios)}</div>' + \
               '<script>' + \
               f'function updateStatus(findingId, statusKey) {{' + \
               '  const formData = new FormData();' + \
               '  formData.append("status_key", statusKey);' + \
               '  fetch("/finding/" + findingId + "/update_status/", {' + \
               '    method: "POST", body: formData,' + \
               '    headers: { "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value }' + \
               '  })' + \
               '  .then(response => response.json())' + \
               '  .then(data => {' + \
               '    if(data.success) { ' + \
               '      console.log("状态更新成功"); ' + \
               '      document.querySelectorAll("input[name=status_" + findingId + "]").forEach(r => r.checked = r.value === statusKey);' + \
               '    } else { ' + \
               '      alert("状态更新失败: " + (data.error || "未知错误")); ' + \
               '    }' + \
               '  })' + \
               '  .catch(error => { alert("请求失败: " + error); });' + \
               '}' + \
               '</script>'
        return mark_safe(html)
    status_radio_group.short_description = '漏洞状态'
    
    def save_model(self, request, obj, form, change):
        """保存漏洞时处理 AI 质量评估"""
        from django.utils import timezone
        
        # 从 POST 数据中获取 AI 质量评估信息
        ai_quality_rating = request.POST.get('ai_quality_rating')
        ai_quality_comment = request.POST.get('ai_quality_comment', '')
        
        # 如果有 AI 质量评估，记录评估人和时间
        if ai_quality_rating:
            # 检查是否是新的评估或评估发生了变化
            if not obj.ai_rated_by or obj.ai_quality_rating != ai_quality_rating or obj.ai_quality_comment != ai_quality_comment:
                obj.ai_quality_rating = ai_quality_rating
                obj.ai_quality_comment = ai_quality_comment
                obj.ai_rated_by = request.user
                obj.ai_rated_at = timezone.now()
        
        super().save_model(request, obj, form, change)
    
    def render_change_form(self, request, context, *args, **kwargs):
        context['back_script'] = mark_safe('<script>document.addEventListener("DOMContentLoaded", function() { const h1 = document.querySelector("h1"); if (h1) { const btn = document.createElement("button"); btn.innerHTML = "← 返回"; btn.style.cssText = "margin-left: 15px; padding: 6px 12px; background: #6c757d; color: white; border: none; border-radius: 4px; font-size: 13px; cursor: pointer;"; btn.onclick = function() { history.back(); }; h1.appendChild(btn); } });</script>')
        return super().render_change_form(request, context, *args, **kwargs)


@admin.register(FindingNote)
class FindingNoteAdmin(admin.ModelAdmin):
    list_display = ['finding', 'author', 'content_preview', 'is_private', 'created_at']
    list_filter = ['is_private', 'created_at', 'author']
    search_fields = ['finding__title', 'content', 'author__username']
    ordering = ['-created_at']
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['back_script'] = mark_safe('<script>document.addEventListener("DOMContentLoaded", function() { const h1 = document.querySelector("h1"); if (h1) { const btn = document.createElement("button"); btn.innerHTML = "← 返回"; btn.style.cssText = "margin-left: 15px; padding: 6px 12px; background: #6c757d; color: white; border: none; border-radius: 4px; font-size: 13px; cursor: pointer;"; btn.onclick = function() { history.back(); }; h1.appendChild(btn); } });</script>')
        return super().changelist_view(request, extra_context)
    
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
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['back_script'] = mark_safe('<script>document.addEventListener("DOMContentLoaded", function() { const h1 = document.querySelector("h1"); if (h1) { const btn = document.createElement("button"); btn.innerHTML = "← 返回"; btn.style.cssText = "margin-left: 15px; padding: 6px 12px; background: #6c757d; color: white; border: none; border-radius: 4px; font-size: 13px; cursor: pointer;"; btn.onclick = function() { history.back(); }; h1.appendChild(btn); } });</script>')
        return super().changelist_view(request, extra_context)


admin.site.site_header = '智能代码安全分析平台'
admin.site.site_title = '代码安全分析管理'
admin.site.index_title = '欢迎使用智能代码安全分析平台'