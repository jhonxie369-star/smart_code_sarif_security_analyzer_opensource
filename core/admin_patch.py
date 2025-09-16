"""
Admin登录绕过补丁
当DISABLE_LOGIN=True时，绕过admin的登录检查
"""
from django.contrib import admin
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpResponseRedirect

# 保存原始的admin_view方法
original_admin_view = admin.AdminSite.admin_view

def patched_admin_view(self, view, cacheable=False):
    """
    修补后的admin_view方法，支持免登录
    """
    def inner(request, *args, **kwargs):
        # 如果禁用了登录功能且用户未登录
        if (getattr(settings, 'DISABLE_LOGIN', False) and 
            not request.user.is_authenticated):
            
            auto_login_user = getattr(settings, 'AUTO_LOGIN_USER', 'admin')
            
            try:
                user = User.objects.get(username=auto_login_user)
                login(request, user)
            except User.DoesNotExist:
                # 如果用户不存在，尝试创建
                try:
                    user = User.objects.create_superuser(
                        username=auto_login_user,
                        email=f'{auto_login_user}@example.com',
                        password='auto_login_password'
                    )
                    login(request, user)
                except Exception:
                    pass  # 忽略创建失败的情况
        
        # 调用原始的admin_view方法
        return original_admin_view(self, view, cacheable)(request, *args, **kwargs)
    
    return inner

# 应用补丁
def apply_admin_patch():
    """应用admin登录绕过补丁"""
    if getattr(settings, 'DISABLE_LOGIN', False):
        admin.AdminSite.admin_view = patched_admin_view
