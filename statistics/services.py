import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from django.db.models import Count, Q, Sum, Case, When, IntegerField, Value
from django.utils import timezone

from core.models import Finding, Project, ScanTask, SeverityManager

logger = logging.getLogger(__name__)


class SecurityStatisticsService:
    """安全统计服务 - 借鉴DefectDojo的统计逻辑"""
    
    @staticmethod
    def get_severity_statistics(queryset) -> Dict:
        """获取严重程度统计 - 三级分级"""
        stats = {
            '高危': 0,
            '中危': 0, 
            '低危': 0,
            'total': 0
        }
        
        # 按严重程度分组统计
        severity_counts = queryset.values('severity').annotate(
            count=Count('id')
        ).order_by('severity')
        
        for item in severity_counts:
            severity = item['severity']
            if severity in stats:
                stats[severity] = item['count']
                stats['total'] += item['count']
        
        return stats
    
    @staticmethod
    def get_status_statistics(queryset) -> Dict:
        """获取状态统计 - 借鉴DefectDojo的状态字段"""
        return {
            'active': queryset.filter(active=True).count(),
            'verified': queryset.filter(verified=True).count(),
            'false_positive': queryset.filter(false_p=True).count(),
            'duplicate': queryset.filter(duplicate=True).count(),
            'out_of_scope': queryset.filter(out_of_scope=True).count(),
            'risk_accepted': queryset.filter(risk_accepted=True).count(),
            'mitigated': queryset.filter(is_mitigated=True).count(),
            'under_review': queryset.filter(under_review=True).count(),
            'total': queryset.count()
        }
    
    @staticmethod
    def get_sla_statistics(queryset) -> Dict:
        """获取SLA统计"""
        sla_stats = {
            'overdue': 0,
            'due_soon': 0,  # 7天内到期
            'on_track': 0,
            'total': 0
        }
        
        active_findings = queryset.filter(active=True, is_mitigated=False)
        
        for finding in active_findings:
            days_remaining = finding.get_sla_days_remaining()
            sla_stats['total'] += 1
            
            if days_remaining <= 0:
                sla_stats['overdue'] += 1
            elif days_remaining <= 7:
                sla_stats['due_soon'] += 1
            else:
                sla_stats['on_track'] += 1
        
        return sla_stats
    
    @staticmethod
    def get_project_statistics(project: Project) -> Dict:
        """获取项目统计信息"""
        findings = Finding.objects.filter(project=project)
        
        return {
            'severity_stats': SecurityStatisticsService.get_severity_statistics(findings),
            'status_stats': SecurityStatisticsService.get_status_statistics(findings),
            'sla_stats': SecurityStatisticsService.get_sla_statistics(findings),
            'scan_stats': SecurityStatisticsService.get_scan_statistics(project),
            'trend_stats': SecurityStatisticsService.get_trend_data(project, days=30)
        }
    
    @staticmethod
    def get_department_statistics(department_name: str) -> Dict:
        """获取部门统计信息"""
        findings = Finding.objects.filter(project__department__name=department_name)
        
        return {
            'severity_stats': SecurityStatisticsService.get_severity_statistics(findings),
            'status_stats': SecurityStatisticsService.get_status_statistics(findings),
            'sla_stats': SecurityStatisticsService.get_sla_statistics(findings),
            'project_breakdown': SecurityStatisticsService.get_project_breakdown(department_name)
        }
    
    @staticmethod
    def get_scan_statistics(project: Project) -> Dict:
        """获取扫描统计"""
        scans = ScanTask.objects.filter(project=project)
        
        return {
            'total_scans': scans.count(),
            'completed_scans': scans.filter(status='completed').count(),
            'failed_scans': scans.filter(status='failed').count(),
            'pending_scans': scans.filter(status='pending').count(),
            'recent_scans': list(scans.order_by('-created_at')[:5].values(
                'id', 'tool_name', 'status', 'total_findings', 'created_at'
            ))
        }
    
    @staticmethod
    def get_project_breakdown(department_name: str) -> List[Dict]:
        """获取部门下项目的漏洞分布"""
        projects = Project.objects.filter(department__name=department_name)
        breakdown = []
        
        for project in projects:
            findings = Finding.objects.filter(project=project)
            severity_stats = SecurityStatisticsService.get_severity_statistics(findings)
            
            breakdown.append({
                'project_id': project.id,
                'project_name': project.name,
                'code_owner': project.code_owner,
                'severity_stats': severity_stats,
                'last_scan': SecurityStatisticsService.get_last_scan_info(project)
            })
        
        return breakdown
    
    @staticmethod
    def get_last_scan_info(project: Project) -> Optional[Dict]:
        """获取最后一次扫描信息"""
        last_scan = ScanTask.objects.filter(project=project).order_by('-created_at').first()
        
        if last_scan:
            return {
                'scan_id': last_scan.id,
                'tool_name': last_scan.tool_name,
                'status': last_scan.status,
                'total_findings': last_scan.total_findings,
                'created_at': last_scan.created_at,
                'completed_at': last_scan.completed_at
            }
        
        return None
    
    @staticmethod
    def get_trend_data(project: Project, days: int = 30) -> List[Dict]:
        """获取趋势数据"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        trend_data = []
        current_date = start_date
        
        while current_date <= end_date:
            # 统计当天新增的漏洞
            daily_new = SecurityStatisticsService.get_severity_statistics(
                Finding.objects.filter(
                    project=project,
                    date=current_date
                )
            )
            
            # 统计当天修复的漏洞
            daily_fixed = Finding.objects.filter(
                project=project,
                mitigated__date=current_date
            ).count()
            
            # 统计当天活跃的漏洞总数
            daily_active = Finding.objects.filter(
                project=project,
                date__lte=current_date,
                active=True
            ).exclude(
                mitigated__date__lt=current_date
            ).count()
            
            trend_data.append({
                'date': current_date.isoformat(),
                'new_findings': daily_new,
                'fixed_count': daily_fixed,
                'active_count': daily_active
            })
            
            current_date += timedelta(days=1)
        
        return trend_data
    
    @staticmethod
    def get_global_statistics() -> Dict:
        """获取全局统计信息"""
        all_findings = Finding.objects.all()
        
        return {
            'total_projects': Project.objects.filter(is_active=True).count(),
            'total_departments': Project.objects.values('department').distinct().count(),
            'severity_stats': SecurityStatisticsService.get_severity_statistics(all_findings),
            'status_stats': SecurityStatisticsService.get_status_statistics(all_findings),
            'sla_stats': SecurityStatisticsService.get_sla_statistics(all_findings),
            'top_vulnerable_projects': SecurityStatisticsService.get_top_vulnerable_projects(),
            'tool_usage_stats': SecurityStatisticsService.get_tool_usage_stats()
        }
    
    @staticmethod
    def get_top_vulnerable_projects(limit: int = 10) -> List[Dict]:
        """获取漏洞最多的项目"""
        projects = Project.objects.annotate(
            total_findings=Count('finding', filter=Q(finding__active=True)),
            high_findings=Count('finding', filter=Q(finding__active=True, finding__severity='高危')),
            medium_findings=Count('finding', filter=Q(finding__active=True, finding__severity='中危'))
        ).filter(
            total_findings__gt=0
        ).order_by('-high_findings', '-medium_findings', '-total_findings')[:limit]
        
        result = []
        for project in projects:
            result.append({
                'project_id': project.id,
                'project_name': project.name,
                'department': project.department.name,
                'code_owner': project.code_owner,
                'total_findings': project.total_findings,
                'high_findings': project.high_findings,
                'medium_findings': project.medium_findings
            })
        
        return result
    
    @staticmethod
    def get_tool_usage_stats() -> Dict:
        """获取工具使用统计"""
        tool_stats = ScanTask.objects.values('tool_name').annotate(
            total_scans=Count('id'),
            completed_scans=Count('id', filter=Q(status='completed')),
            total_findings=Sum('total_findings')
        ).order_by('-total_scans')
        
        return {
            'tool_breakdown': list(tool_stats),
            'most_used_tool': tool_stats.first()['tool_name'] if tool_stats else None
        }
    
    @staticmethod
    def get_ai_analysis_stats() -> Dict:
        """获取AI分析统计"""
        findings_with_ai = Finding.objects.exclude(ai_analysis={})
        
        return {
            'total_analyzed': findings_with_ai.count(),
            'cached_results': findings_with_ai.filter(ai_cached=True).count(),
            'analysis_coverage': (findings_with_ai.count() / Finding.objects.count() * 100) if Finding.objects.count() > 0 else 0
        }
    
    @staticmethod
    def get_translation_stats() -> Dict:
        """获取翻译统计"""
        translated_findings = Finding.objects.exclude(translated_message='').exclude(translated_message=None)
        
        return {
            'total_translated': translated_findings.count(),
            'translation_coverage': (translated_findings.count() / Finding.objects.count() * 100) if Finding.objects.count() > 0 else 0
        }


class ReportGenerator:
    """报告生成器"""
    
    @staticmethod
    def generate_project_report(project: Project) -> Dict:
        """生成项目报告"""
        stats = SecurityStatisticsService.get_project_statistics(project)
        
        return {
            'project_info': {
                'name': project.name,
                'department': project.department.name,
                'code_owner': project.code_owner,
                'tech_lead': project.tech_lead,
                'business_criticality': project.business_criticality
            },
            'statistics': stats,
            'generated_at': timezone.now().isoformat(),
            'summary': ReportGenerator._generate_summary(stats)
        }
    
    @staticmethod
    def generate_department_report(department_name: str) -> Dict:
        """生成部门报告"""
        stats = SecurityStatisticsService.get_department_statistics(department_name)
        
        return {
            'department_name': department_name,
            'statistics': stats,
            'generated_at': timezone.now().isoformat(),
            'summary': ReportGenerator._generate_summary(stats)
        }
    
    @staticmethod
    def _generate_summary(stats: Dict) -> Dict:
        """生成统计摘要"""
        severity_stats = stats.get('severity_stats', {})
        sla_stats = stats.get('sla_stats', {})
        
        return {
            'total_findings': severity_stats.get('total', 0),
            'high_risk_findings': severity_stats.get('高危', 0) + severity_stats.get('中危', 0),
            'overdue_findings': sla_stats.get('overdue', 0),
            'risk_level': ReportGenerator._calculate_risk_level(severity_stats, sla_stats)
        }
    
    @staticmethod
    def _calculate_risk_level(severity_stats: Dict, sla_stats: Dict) -> str:
        """计算风险等级"""
        high_count = severity_stats.get('高危', 0)
        medium_count = severity_stats.get('中危', 0)
        overdue_count = sla_stats.get('overdue', 0)
        
        if high_count > 0 or overdue_count > 5:
            return 'critical'
        elif medium_count > 5 or overdue_count > 0:
            return 'high'
        elif severity_stats.get('低危', 0) > 10:
            return 'medium'
        else:
            return 'low'
