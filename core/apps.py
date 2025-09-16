from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """应用启动时的初始化"""
        # 暴力禁用admin登录
        from .disable_login_patch import disable_admin_login
        disable_admin_login()
    verbose_name = '核心模块'
