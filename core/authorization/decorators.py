"""
基于 DefectDojo 设计的授权装饰器
"""
import functools
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings

from .authorization import (
    user_has_permission_or_403,
    user_has_global_permission_or_403,
    user_has_configuration_permission,
)


def user_is_authorized(model, permission, arg, lookup="pk", func=None):
    """装饰器：确保用户对指定对象有权限"""
    if func is None:
        return functools.partial(
            user_is_authorized, model, permission, arg, lookup,
        )

    @functools.wraps(func)
    def _wrapped(request, *args, **kwargs):
        # 如果禁用了登录，跳过权限检查
        if getattr(settings, 'DISABLE_LOGIN', False):
            return func(request, *args, **kwargs)
        
        # 从参数中获取对象ID
        if isinstance(arg, int):
            # 位置参数
            args_list = list(args)
            lookup_value = args_list[arg]
        else:
            # 关键字参数
            lookup_value = kwargs.get(arg)

        # 获取对象
        obj = get_object_or_404(model.objects.filter(**{lookup: lookup_value}))

        # 检查权限
        user_has_permission_or_403(request.user, obj, permission)

        return func(request, *args, **kwargs)

    return _wrapped


def user_has_global_permission(permission, func=None):
    """装饰器：确保用户有全局权限"""
    if func is None:
        return functools.partial(user_has_global_permission, permission)

    @functools.wraps(func)
    def _wrapped(request, *args, **kwargs):
        # 如果禁用了登录，跳过权限检查
        if getattr(settings, 'DISABLE_LOGIN', False):
            return func(request, *args, **kwargs)
        
        user_has_global_permission_or_403(request.user, permission)
        return func(request, *args, **kwargs)

    return _wrapped


def user_is_configuration_authorized(permission, func=None):
    """装饰器：检查用户是否有配置权限"""
    if func is None:
        return functools.partial(user_is_configuration_authorized, permission)

    @functools.wraps(func)
    def _wrapped(request, *args, **kwargs):
        # 如果禁用了登录，跳过权限检查
        if getattr(settings, 'DISABLE_LOGIN', False):
            return func(request, *args, **kwargs)
        
        if not user_has_configuration_permission(request.user, permission):
            raise PermissionDenied("用户没有配置权限")
        return func(request, *args, **kwargs)

    return _wrapped


def smart_login_required(func=None):
    """智能登录装饰器：根据配置决定是否需要登录"""
    if func is None:
        return functools.partial(smart_login_required)

    @functools.wraps(func)
    def _wrapped(request, *args, **kwargs):
        # 如果禁用了登录，直接执行函数
        if getattr(settings, 'DISABLE_LOGIN', False):
            return func(request, *args, **kwargs)
        
        # 否则使用标准的登录装饰器
        return login_required(func)(request, *args, **kwargs)

    return _wrapped


def require_permission(permission):
    """装饰器：要求指定权限"""
    def decorator(func):
        @functools.wraps(func)
        @smart_login_required
        def _wrapped(request, *args, **kwargs):
            # 如果禁用了登录，跳过权限检查
            if getattr(settings, 'DISABLE_LOGIN', False):
                return func(request, *args, **kwargs)
            
            user_has_global_permission_or_403(request.user, permission)
            return func(request, *args, **kwargs)
        return _wrapped
    return decorator