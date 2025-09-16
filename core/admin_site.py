from django.contrib import admin
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.conf import settings
from django.urls import reverse

class NoLoginAdminSite(admin.AdminSite):
    """
    自定义Admin站点，支持免登录访问
    """
    
    def admin_view(self, view, cacheable=False):
        """
        重写admin_view方法，在禁用登录时自动登录用户
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
            
            return super(NoLoginAdminSite, self).admin_view(view, cacheable)(request, *args, **kwargs)
        
        return inner
    
    def login(self, request, extra_context=None):
        """
        重写登录方法，在禁用登录时直接跳转到admin首页
        """
        if getattr(settings, 'DISABLE_LOGIN', False):
            auto_login_user = getattr(settings, 'AUTO_LOGIN_USER', 'admin')
            
            try:
                user = User.objects.get(username=auto_login_user)
                login(request, user)
            except User.DoesNotExist:
                try:
                    user = User.objects.create_superuser(
                        username=auto_login_user,
                        email=f'{auto_login_user}@example.com',
                        password='auto_login_password'
                    )
                    login(request, user)
                except Exception:
                    pass
            
            return HttpResponseRedirect(reverse('admin:index'))
        
        return super().login(request, extra_context)

# 创建自定义admin站点实例
admin_site = NoLoginAdminSite(name='admin')
