from django.contrib.auth import login
from django.contrib.auth.models import User
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse

class AutoLoginMiddleware:
    """
    自动登录中间件
    当DISABLE_LOGIN=True时，自动以指定用户身份登录
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 如果禁用了登录功能
        if getattr(settings, 'DISABLE_LOGIN', False):
            # 检查是否是admin登录页面，直接跳转到admin首页
            if request.path == '/admin/login/':
                return HttpResponseRedirect('/admin/')
            
            # 如果用户未登录，自动登录
            if not request.user.is_authenticated:
                auto_login_user = getattr(settings, 'AUTO_LOGIN_USER', 'admin')
                
                try:
                    user = User.objects.get(username=auto_login_user)
                    login(request, user)
                except User.DoesNotExist:
                    # 如果用户不存在，尝试创建
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
                        pass  # 忽略创建失败的情况

        response = self.get_response(request)
        return response
