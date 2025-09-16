"""
动态登录热补丁系统 - 支持运行时切换登录模式
"""
import os
from django.contrib import admin
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpResponseRedirect

# 存储原始方法的全局变量
_original_methods = {}
_patch_applied = False

def _get_current_login_setting():
    """动态读取当前登录设置"""
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('DISABLE_LOGIN='):
                    return line.split('=', 1)[1].lower() == 'true'
    return getattr(settings, 'DISABLE_LOGIN', False)

def _save_original_methods():
    """保存原始方法"""
    global _original_methods
    if not _original_methods:
        _original_methods = {
            'admin_view': admin.AdminSite.admin_view,
            'has_permission': admin.AdminSite.has_permission,
            'login': admin.AdminSite.login,
        }

def _restore_original_methods():
    """恢复原始方法"""
    global _original_methods, _patch_applied
    if _original_methods:
        admin.AdminSite.admin_view = _original_methods['admin_view']
        admin.AdminSite.has_permission = _original_methods['has_permission']
        admin.AdminSite.login = _original_methods['login']
        _patch_applied = False

def _apply_no_login_patch():
    """应用无登录补丁"""
    global _patch_applied
    
    def no_login_admin_view(self, view, cacheable=False):
        def inner(request, *args, **kwargs):
            # 动态检查登录设置
            if _get_current_login_setting():
                # 如果用户未登录，自动创建并登录admin用户
                if not request.user.is_authenticated:
                    auto_login_user = getattr(settings, 'AUTO_LOGIN_USER', 'admin')
                    try:
                        user = User.objects.get(username=auto_login_user)
                    except User.DoesNotExist:
                        # 从环境变量获取默认密码，或使用随机密码
                        import os
                        import secrets
                        default_password = os.getenv('AUTO_LOGIN_PASSWORD', secrets.token_urlsafe(12))
                        user = User.objects.create_superuser(
                            username=auto_login_user,
                            email=f'{auto_login_user}@example.com',
                            password=default_password
                        )
                    login(request, user)
                
                # 直接调用视图，跳过权限检查
                return view(request, *args, **kwargs)
            else:
                # 如果登录已启用，使用原始方法
                return _original_methods['admin_view'](self, view, cacheable)(request, *args, **kwargs)
        return inner
    
    def dynamic_has_permission(self, request):
        """动态权限检查"""
        if _get_current_login_setting():
            return True  # 禁用登录时总是有权限
        else:
            return _original_methods['has_permission'](self, request)
    
    def dynamic_login(self, request, extra_context=None):
        """动态登录处理"""
        if _get_current_login_setting():
            # 禁用登录时，自动登录并重定向
            if not request.user.is_authenticated:
                auto_login_user = getattr(settings, 'AUTO_LOGIN_USER', 'admin')
                try:
                    user = User.objects.get(username=auto_login_user)
                    login(request, user)
                except User.DoesNotExist:
                    try:
                        # 从环境变量获取默认密码，或使用随机密码
                        import os
                        import secrets
                        default_password = os.getenv('AUTO_LOGIN_PASSWORD', secrets.token_urlsafe(12))
                        user = User.objects.create_superuser(
                            username=auto_login_user,
                            email=f'{auto_login_user}@example.com',
                            password=default_password
                        )
                        login(request, user)
                    except Exception:
                        pass
            return HttpResponseRedirect('/admin/')
        else:
            # 启用登录时，使用原始登录方法
            return _original_methods['login'](self, request, extra_context)
    
    # 应用动态补丁
    admin.AdminSite.admin_view = no_login_admin_view
    admin.AdminSite.has_permission = dynamic_has_permission
    admin.AdminSite.login = dynamic_login
    _patch_applied = True

def apply_dynamic_login_patch():
    """应用动态登录补丁 - 支持热切换"""
    _save_original_methods()
    _apply_no_login_patch()
    
    current_setting = _get_current_login_setting()
    if current_setting:
        print("✓ 动态登录补丁已激活 - 当前模式：自动登录")
    else:
        print("✓ 动态登录补丁已激活 - 当前模式：正常登录")
    print("  补丁支持运行时热切换，无需重启服务")

def disable_admin_login():
    """兼容旧接口"""
    apply_dynamic_login_patch()
