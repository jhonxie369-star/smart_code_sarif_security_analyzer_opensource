"""
基于 DefectDojo 设计的授权系统核心逻辑
"""
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser

from .roles_permissions import Permissions, get_user_permissions


def user_has_permission(user, obj, permission):
    """检查用户是否对指定对象有权限"""
    if isinstance(user, AnonymousUser):
        return False
    
    if user.is_superuser:
        return True
    
    # 获取用户权限
    user_permissions = get_user_permissions(user)
    
    # 检查是否有指定权限
    if permission not in user_permissions:
        return False
    
    # 这里可以扩展为基于对象的权限检查
    # 例如：用户只能访问自己部门的项目
    return True


def user_has_global_permission(user, permission):
    """检查用户是否有全局权限"""
    if isinstance(user, AnonymousUser):
        return False
    
    if user.is_superuser:
        return True
    
    user_permissions = get_user_permissions(user)
    return permission in user_permissions


def user_has_permission_or_403(user, obj, permission):
    """检查权限，如果没有权限则抛出403异常"""
    if not user_has_permission(user, obj, permission):
        raise PermissionDenied(f"用户没有权限执行此操作")


def user_has_global_permission_or_403(user, permission):
    """检查全局权限，如果没有权限则抛出403异常"""
    if not user_has_global_permission(user, permission):
        raise PermissionDenied(f"用户没有权限执行此操作")


def user_has_configuration_permission(user, permission):
    """检查用户是否有配置权限"""
    if isinstance(user, AnonymousUser):
        return False
    
    if user.is_superuser:
        return True
    
    # 检查Django内置权限
    return user.has_perm(permission)


def get_accessible_departments(user):
    """获取用户可访问的部门列表"""
    from core.models import Department
    
    if user.is_superuser:
        return Department.objects.all()
    
    # 这里可以扩展为基于用户角色的部门过滤
    # 目前返回所有部门
    return Department.objects.all()


def get_accessible_projects(user, department=None):
    """获取用户可访问的项目列表"""
    from core.models import Project
    
    if user.is_superuser:
        queryset = Project.objects.all()
    else:
        # 这里可以扩展为基于用户角色的项目过滤
        queryset = Project.objects.all()
    
    if department:
        queryset = queryset.filter(department=department)
    
    return queryset


def filter_queryset_by_permission(user, queryset, permission):
    """根据权限过滤查询集"""
    if user.is_superuser:
        return queryset
    
    if not user_has_global_permission(user, permission):
        return queryset.none()
    
    # 这里可以扩展为更细粒度的过滤
    return queryset