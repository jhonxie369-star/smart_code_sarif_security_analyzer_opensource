"""
API 权限类
"""
from rest_framework import permissions
from django.conf import settings
from core.authorization.authorization import user_has_global_permission
from core.authorization.roles_permissions import Permissions


class SmartIsAuthenticated(permissions.BasePermission):
    """智能认证权限：根据配置决定是否需要认证"""
    
    def has_permission(self, request, view):
        # 如果禁用了登录，允许所有访问
        if getattr(settings, 'DISABLE_LOGIN', False):
            return True
        
        # 否则检查用户是否已认证
        return request.user and request.user.is_authenticated


class HasGlobalPermission(permissions.BasePermission):
    """检查用户是否有全局权限"""
    
    def __init__(self, permission):
        self.permission = permission
    
    def has_permission(self, request, view):
        # 如果禁用了登录，允许所有访问
        if getattr(settings, 'DISABLE_LOGIN', False):
            return True
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        return user_has_global_permission(request.user, self.permission)


class DepartmentPermission(permissions.BasePermission):
    """部门权限"""
    
    def has_permission(self, request, view):
        if getattr(settings, 'DISABLE_LOGIN', False):
            return True
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 根据请求方法确定所需权限
        if request.method in permissions.SAFE_METHODS:
            required_permission = Permissions.DEPARTMENT_VIEW
        elif request.method == 'POST':
            required_permission = Permissions.DEPARTMENT_ADD
        elif request.method in ['PUT', 'PATCH']:
            required_permission = Permissions.DEPARTMENT_EDIT
        elif request.method == 'DELETE':
            required_permission = Permissions.DEPARTMENT_DELETE
        else:
            return False
        
        return user_has_global_permission(request.user, required_permission)


class ProjectPermission(permissions.BasePermission):
    """项目权限"""
    
    def has_permission(self, request, view):
        if getattr(settings, 'DISABLE_LOGIN', False):
            return True
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 根据请求方法确定所需权限
        if request.method in permissions.SAFE_METHODS:
            required_permission = Permissions.PROJECT_VIEW
        elif request.method == 'POST':
            required_permission = Permissions.PROJECT_ADD
        elif request.method in ['PUT', 'PATCH']:
            required_permission = Permissions.PROJECT_EDIT
        elif request.method == 'DELETE':
            required_permission = Permissions.PROJECT_DELETE
        else:
            return False
        
        return user_has_global_permission(request.user, required_permission)


class ScanPermission(permissions.BasePermission):
    """扫描权限"""
    
    def has_permission(self, request, view):
        if getattr(settings, 'DISABLE_LOGIN', False):
            return True
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 根据请求方法确定所需权限
        if request.method in permissions.SAFE_METHODS:
            required_permission = Permissions.SCAN_VIEW
        elif request.method == 'POST':
            required_permission = Permissions.SCAN_ADD
        elif request.method in ['PUT', 'PATCH']:
            required_permission = Permissions.SCAN_EDIT
        elif request.method == 'DELETE':
            required_permission = Permissions.SCAN_DELETE
        else:
            return False
        
        return user_has_global_permission(request.user, required_permission)


class FindingPermission(permissions.BasePermission):
    """漏洞权限"""
    
    def has_permission(self, request, view):
        if getattr(settings, 'DISABLE_LOGIN', False):
            return True
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 根据请求方法确定所需权限
        if request.method in permissions.SAFE_METHODS:
            required_permission = Permissions.FINDING_VIEW
        elif request.method == 'POST':
            required_permission = Permissions.FINDING_ADD
        elif request.method in ['PUT', 'PATCH']:
            required_permission = Permissions.FINDING_EDIT
        elif request.method == 'DELETE':
            required_permission = Permissions.FINDING_DELETE
        else:
            return False
        
        return user_has_global_permission(request.user, required_permission)