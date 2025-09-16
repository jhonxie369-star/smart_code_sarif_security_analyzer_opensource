import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import SmartIsAuthenticated, DepartmentPermission, ProjectPermission, ScanPermission, FindingPermission
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from datetime import datetime

from core.models import Project, Finding, ScanTask, Department
from .serializers import (
    ProjectSerializer, FindingSerializer, ScanTaskSerializer, 
    DepartmentSerializer, FindingDetailSerializer
)
from statistics.services import SecurityStatisticsService, ReportGenerator
from ai_analysis.services import ai_analysis_service
from translation.services import translation_service
from parsers.sarif_parser import parse_sarif_file
from django.utils import timezone
from core.authorization.authorization import filter_queryset_by_permission
from core.authorization.roles_permissions import Permissions

logger = logging.getLogger(__name__)


class DepartmentViewSet(viewsets.ModelViewSet):
    """部门视图集"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [DepartmentPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取部门统计信息"""
        department = self.get_object()
        stats = SecurityStatisticsService.get_department_statistics(department.name)
        return Response(stats)
    
    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """生成部门报告"""
        department = self.get_object()
        report = ReportGenerator.generate_department_report(department.name)
        return Response(report)


class ProjectViewSet(viewsets.ModelViewSet):
    """项目视图集"""
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [ProjectPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['department', 'business_criticality', 'is_active']
    search_fields = ['name', 'description', 'code_owner']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['department__name', 'name']
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取项目统计信息"""
        project = self.get_object()
        stats = SecurityStatisticsService.get_project_statistics(project)
        return Response(stats)
    
    @action(detail=True, methods=['get'])
    def findings(self, request, pk=None):
        """获取项目的漏洞列表"""
        project = self.get_object()
        findings = Finding.objects.filter(project=project)
        
        # 应用过滤器
        severity = request.query_params.get('severity')
        if severity:
            findings = findings.filter(severity=severity)
        
        status_filter = request.query_params.get('status')
        if status_filter == 'active':
            findings = findings.filter(active=True)
        elif status_filter == 'mitigated':
            findings = findings.filter(is_mitigated=True)
        elif status_filter == 'false_positive':
            findings = findings.filter(false_p=True)
        
        # 分页
        page = self.paginate_queryset(findings)
        if page is not None:
            serializer = FindingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = FindingSerializer(findings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """生成项目报告"""
        project = self.get_object()
        report = ReportGenerator.generate_project_report(project)
        return Response(report)
    
    @action(detail=True, methods=['post'])
    def auto_scan(self, request, pk=None):
        """自动扫描项目"""
        project = self.get_object()
        git_url = request.data.get('git_url') or project.git_url
        branch = request.data.get('branch') or project.git_branch or 'main'
        language = request.data.get('language')  # 用户指定的语言
        
        if not git_url:
            return Response(
                {'error': '请提供Git仓库地址'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from core.scanner import AutoScanner
            from core.scan_queue import scan_queue
            
            # 创建扫描任务
            scan_task = ScanTask.objects.create(
                project=project,
                tool_name='auto',
                scan_type='full',
                status='pending'
            )
            
            # 创建扫描函数（不再创建新任务）
            def scan_func():
                scanner = AutoScanner(project)
                # 直接调用扫描逻辑，传入已存在的scan_task和语言参数
                return scanner.execute_scan(git_url, branch, scan_task, language)
            
            # 添加到队列
            scan_queue.add_task(scan_task.id, scan_func)
            
            return Response({
                'success': True,
                'scan_task_id': scan_task.id,
                'message': '扫描任务已加入队列',
                'queue_status': scan_queue.get_queue_status()
            })
            
        except Exception as e:
            logger.error(f"自动扫描失败: {e}")
            return Response(
                {'success': False, 'error': f'自动扫描失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def check_updates(self, request, pk=None):
        """检查Git更新"""
        project = self.get_object()
        
        if not project.git_url:
            return Response({'error': '项目未配置Git地址'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from core.scanner import AutoScanner
            scanner = AutoScanner(project)
            has_updates = scanner.check_git_updates(project.git_url, project.git_branch)
            
            return Response({
                'has_updates': has_updates,
                'git_url': project.git_url,
                'branch': project.git_branch
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScanTaskViewSet(viewsets.ModelViewSet):
    """扫描任务视图集"""
    queryset = ScanTask.objects.all()
    serializer_class = ScanTaskSerializer
    permission_classes = [ScanPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'tool_name', 'status']
    search_fields = ['project__name', 'tool_name']
    ordering_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """获取扫描日志"""
        scan_task = self.get_object()
        
        # 支持实时查询
        last_line = int(request.query_params.get('last_line', 0))
        logs = scan_task.scan_log.split('\n') if scan_task.scan_log else []
        
        if last_line < len(logs):
            new_logs = logs[last_line:]
        else:
            new_logs = []
            
        return Response({
            'logs': new_logs,
            'total_lines': len(logs),
            'status': scan_task.status,
            'error_message': scan_task.error_message,
            'is_running': scan_task.status == 'running'
        })
    
    @action(detail=True, methods=['post'])
    def manual_scan(self, request, pk=None):
        """手动扫描 - 仅解析已存在的报告"""
        scan_task = self.get_object()
        
        if not scan_task.report_file or not os.path.exists(scan_task.report_file):
            return Response(
                {'error': '报告文件不存在'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            scan_task.status = 'running'
            scan_task.manual_scan = True
            scan_task.save()
            
            from core.models import Finding
            findings = parse_sarif_file(scan_task.report_file, scan_task.project, scan_task)
            Finding.objects.bulk_create(findings)
            
            scan_task.status = 'completed'
            scan_task.total_findings = len(findings)
            scan_task.save()
            
            return Response({
                'message': f'手动解析完成，共{len(findings)}个漏洞',
                'findings_count': len(findings)
            })
            
        except Exception as e:
            scan_task.status = 'failed'
            scan_task.error_message = str(e)
            scan_task.save()
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def kill_task(self, request, pk=None):
        """终止扫描任务"""
        scan_task = self.get_object()
        
        if scan_task.status != 'running':
            return Response(
                {'error': '只能终止运行中的任务'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            import subprocess
            import os
            
            project_id = scan_task.project.id
            from django.conf import settings
            project_path = os.path.join(settings.AUTO_SCAN_CONFIG['PROJECT_DIR'], scan_task.project.department.name, scan_task.project.name)
            
            # 1. 杀死所有包含项目路径的进程
            subprocess.run(f"pkill -9 -f '{project_path}' 2>/dev/null || true", shell=True)
            
            # 2. 杀死所有包含项目 ID 的进程
            subprocess.run(f"pkill -9 -f 'scan_{project_id}' 2>/dev/null || true", shell=True)
            
            # 3. 杀死所有扫描工具进程
            subprocess.run("pkill -9 -f 'codeql.*database.*create' 2>/dev/null || true", shell=True)
            subprocess.run("pkill -9 -f 'codeql.*analyze' 2>/dev/null || true", shell=True)
            subprocess.run("pkill -9 -f 'semgrep.*--sarif' 2>/dev/null || true", shell=True)
            
            # 4. 杀死在项目目录下的npm/node进程
            subprocess.run(f"lsof +D '{project_path}' 2>/dev/null | awk 'NR>1 {{print $2}}' | xargs -r kill -9 2>/dev/null || true", shell=True)
            
            # 5. 杀死包含项目名的npm进程
            subprocess.run(f"pkill -9 -f 'npm.*{scan_task.project.name}' 2>/dev/null || true", shell=True)
            
            # 6. 全面清理临时文件和目录
            work_dir = settings.AUTO_SCAN_CONFIG['WORK_DIR']
            temp_dirs = [
                f"{work_dir}/scan_{project_id}",
                f"{work_dir}/codeql-db-*",
                f"{settings.BASE_DIR}/logs/scan_{project_id}*"
            ]
            
            for temp_dir in temp_dirs:
                subprocess.run(f"rm -rf {temp_dir} 2>/dev/null || true", shell=True)
            
            # 7. 清理可能的锁文件
            subprocess.run(f"rm -f {project_path}/.git/index.lock 2>/dev/null || true", shell=True)
            subprocess.run(f"rm -f {project_path}/package-lock.json.* 2>/dev/null || true", shell=True)
            
            # 8. 更新任务状态
            scan_task.status = 'failed'
            scan_task.error_message = '用户手动终止任务'
            scan_task.save()
            
            # 9. 记录终止日志
            if scan_task.scan_log:
                scan_task.scan_log += f"\n{datetime.now().strftime('%H:%M:%S')} [KILL] 任务已被终止，所有相关进程已清理"
            else:
                scan_task.scan_log = f"{datetime.now().strftime('%H:%M:%S')} [KILL] 任务已被终止"
            scan_task.save()
            
            return Response({'message': '任务已终止'})
            
        except Exception as e:
            return Response(
                {'error': f'终止任务失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def parse_report(self, request, pk=None):
        """解析扫描报告"""
        scan_task = self.get_object()
        
        if not scan_task.report_file:
            return Response(
                {'error': '扫描任务没有关联的报告文件'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 更新任务状态
            scan_task.status = 'running'
            scan_task.save()
            
            # 解析SARIF文件
            findings = parse_sarif_file(
                scan_task.report_file, 
                scan_task.project, 
                scan_task
            )
            
            # 批量创建漏洞记录
            Finding.objects.bulk_create(findings)
            
            # 更新统计信息 - 三级分级
            scan_task.total_findings = len(findings)
            scan_task.critical_count = sum(1 for f in findings if f.severity == '高危')
            scan_task.high_count = sum(1 for f in findings if f.severity == '中危')
            scan_task.medium_count = sum(1 for f in findings if f.severity == '低危')
            scan_task.low_count = 0  # 不再使用
            scan_task.info_count = 0  # 不再使用
            scan_task.status = 'completed'
            scan_task.save()
            
            return Response({
                'message': f'成功解析 {len(findings)} 个漏洞',
                'statistics': {
                    'total': len(findings),
                    '高危': scan_task.critical_count,
                    '中危': scan_task.high_count,
                    '低危': scan_task.medium_count
                }
            })
            
        except Exception as e:
            logger.error(f"Error parsing report for scan {scan_task.id}: {e}")
            scan_task.status = 'failed'
            scan_task.error_message = str(e)
            scan_task.save()
            
            return Response(
                {'error': f'解析报告失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FindingViewSet(viewsets.ModelViewSet):
    """漏洞发现视图集"""
    queryset = Finding.objects.all()
    serializer_class = FindingSerializer
    permission_classes = [FindingPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        'project', 'severity', 'active', 'verified', 'false_p', 
        'duplicate', 'is_mitigated', 'risk_accepted'
    ]
    search_fields = ['title', 'description', 'file_path', 'code_owner']
    ordering_fields = ['severity', 'date', 'created_at']
    ordering = ['-numerical_severity', '-date']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FindingDetailSerializer
        return FindingSerializer
    
    @action(detail=True, methods=['post'])
    def ai_analyze(self, request, pk=None):
        """AI分析单个漏洞"""
        finding = self.get_object()
        
        try:
            result = ai_analysis_service.analyze_finding(finding)
            
            # 更新漏洞的AI分析结果
            if 'analysis' in result and result['analysis'].get('success'):
                finding.ai_analysis = result['analysis']
                finding.ai_cached = result['cached']
                finding.save()
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"AI analysis failed for finding {finding.id}: {e}")
            return Response(
                {'error': f'AI分析失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def batch_ai_analyze(self, request):
        """批量AI分析"""
        finding_ids = request.data.get('finding_ids', [])
        rule_id = request.data.get('rule_id', 'unknown')
        
        if not finding_ids:
            return Response(
                {'error': '请提供要分析的漏洞ID列表'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            findings = Finding.objects.filter(id__in=finding_ids)
            result = ai_analysis_service.batch_analyze_findings(findings, rule_id)
            
            # 更新所有漏洞的AI分析结果
            if 'analysis' in result and result['analysis'].get('success'):
                for finding in findings:
                    finding.ai_analysis = result['analysis']
                    finding.ai_cached = result['cached']
                    finding.save()
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Batch AI analysis failed: {e}")
            return Response(
                {'error': f'批量AI分析失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def translate(self, request, pk=None):
        """翻译漏洞描述"""
        finding = self.get_object()
        
        try:
            if not finding.translated_message:
                translated = translation_service.translate_text(finding.message)
                finding.translated_message = translated
                finding.save()
            
            return Response({
                'original': finding.message,
                'translated': finding.translated_message,
                'cached': bool(finding.translated_message)
            })
            
        except Exception as e:
            logger.error(f"Translation failed for finding {finding.id}: {e}")
            return Response(
                {'error': f'翻译失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """更新漏洞状态"""
        finding = self.get_object()
        new_status = request.data.get('status')
        reason = request.data.get('reason', '')
        
        valid_statuses = {
            'verified': 'verified',
            'false_positive': 'false_p',
            'mitigated': 'is_mitigated',
            'risk_accepted': 'risk_accepted',
            'duplicate': 'duplicate',
            'out_of_scope': 'out_of_scope'
        }
        
        if new_status not in valid_statuses:
            return Response(
                {'error': f'无效的状态: {new_status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 记录状态变更历史
            from core.models import StatusHistory
            
            old_status = 'active' if finding.active else 'inactive'
            
            # 更新状态
            setattr(finding, valid_statuses[new_status], True)
            if new_status == 'mitigated':
                finding.mitigated = timezone.now()
            finding.save()
            
            # 创建状态历史记录
            StatusHistory.objects.create(
                finding=finding,
                from_status=old_status,
                to_status=new_status,
                changed_by=request.user,
                reason=reason
            )
            
            return Response({
                'message': f'状态已更新为: {new_status}',
                'status': new_status
            })
            
        except Exception as e:
            logger.error(f"Status update failed for finding {finding.id}: {e}")
            return Response(
                {'error': f'状态更新失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取漏洞统计信息"""
        queryset = self.filter_queryset(self.get_queryset())
        
        stats = {
            'severity_stats': SecurityStatisticsService.get_severity_statistics(queryset),
            'status_stats': SecurityStatisticsService.get_status_statistics(queryset),
            'sla_stats': SecurityStatisticsService.get_sla_statistics(queryset)
        }
        
        return Response(stats)


class GlobalStatisticsViewSet(viewsets.ViewSet):
    """全局统计视图集"""
    permission_classes = [SmartIsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """获取全局概览统计"""
        stats = SecurityStatisticsService.get_global_statistics()
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def ai_stats(self, request):
        """获取AI分析统计"""
        stats = SecurityStatisticsService.get_ai_analysis_stats()
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def translation_stats(self, request):
        """获取翻译统计"""
        stats = SecurityStatisticsService.get_translation_stats()
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def top_projects(self, request):
        """获取漏洞最多的项目"""
        limit = int(request.query_params.get('limit', 10))
        projects = SecurityStatisticsService.get_top_vulnerable_projects(limit)
        return Response(projects)
    
    @action(detail=False, methods=['get'])
    def queue_status(self, request):
        """获取扫描队列状态"""
        from core.scan_queue import scan_queue
        return Response(scan_queue.get_queue_status())



