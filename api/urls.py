from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet, ProjectViewSet, ScanTaskViewSet, 
    FindingViewSet, GlobalStatisticsViewSet
)
from .documentation_views import api_overview_view, api_docs_view
from .login_control import login_control_api
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from core.authorization.decorators import smart_login_required, require_permission
from core.authorization.roles_permissions import Permissions
import os
import subprocess

@require_permission(Permissions.SCAN_VIEW)
def scan_logs_view(request):
    return render(request, 'api/scan_logs.html')

@require_permission(Permissions.PROJECT_SCAN)
def quick_scan_view(request):
    return render(request, 'scan/quick_scan.html')

@require_permission(Permissions.SCAN_VIEW)
def task_monitor_view(request):
    return render(request, 'scan/task_monitor.html')

@require_permission(Permissions.SYSTEM_LOGS)
def error_logs_view(request):
    return render(request, 'admin/error_logs.html')

@require_permission(Permissions.SYSTEM_LOGS)
def system_logs_api(request):
    if request.method == 'GET':
        level = request.GET.get('level', 'all')
        lines = int(request.GET.get('lines', 100))
        
        try:
            from django.conf import settings
            log_file = settings.BASE_DIR / 'logs' / 'django.log'
            
            if not os.path.exists(log_file):
                return JsonResponse({'logs': '日志文件不存在'})
            
            # 读取最后N行
            cmd = f'tail -n {lines} {log_file}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            logs = result.stdout
            
            # 按级别过滤
            if level != 'all':
                filtered_logs = []
                for line in logs.split('\n'):
                    if level in line:
                        filtered_logs.append(line)
                logs = '\n'.join(filtered_logs)
            
            return JsonResponse({'logs': logs})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    elif request.method == 'DELETE':
        try:
            from django.conf import settings
            log_file = settings.BASE_DIR / 'logs' / 'django.log'
            if os.path.exists(log_file):
                with open(log_file, 'w') as f:
                    f.write('')
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


router = DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'scans', ScanTaskViewSet)
router.register(r'findings', FindingViewSet)
router.register(r'statistics', GlobalStatisticsViewSet, basename='statistics')

urlpatterns = [
    path('', api_docs_view, name='api-root'),
    path('v1/', include(router.urls)),
    path('auth/', include('rest_framework.urls')),

    path('overview/', api_overview_view, name='api_overview'),

    path('docs/', api_docs_view, name='api_docs'),
    path('scan-logs/', scan_logs_view, name='scan_logs'),
    path('quick-scan/', quick_scan_view, name='quick_scan'),
    path('task-monitor/', task_monitor_view, name='task_monitor'),
    path('error-logs/', error_logs_view, name='error_logs'),
    path('system-logs/', system_logs_api, name='system_logs'),
    path('login-control/', login_control_api, name='login_control'),
]
