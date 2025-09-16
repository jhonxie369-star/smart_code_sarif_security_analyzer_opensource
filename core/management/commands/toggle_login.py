import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = '切换登录模式'

    def add_arguments(self, parser):
        parser.add_argument(
            '--disable',
            action='store_true',
            help='禁用登录功能',
        )
        parser.add_argument(
            '--enable',
            action='store_true',
            help='启用登录功能',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='查看当前登录状态',
        )

    def handle(self, *args, **options):
        env_file = '.env'
        
        if options['status']:
            self.show_status()
            return
        
        if options['disable']:
            self.update_env_file(env_file, 'DISABLE_LOGIN', 'True')
            self.stdout.write(self.style.SUCCESS('✓ 已禁用登录功能（热切换）'))
            self.stdout.write('用户将自动以admin身份登录')
            self.stdout.write('✓ 更改已立即生效，无需重启服务')
            
        elif options['enable']:
            self.update_env_file(env_file, 'DISABLE_LOGIN', 'False')
            self.stdout.write(self.style.SUCCESS('✓ 已启用登录功能（热切换）'))
            self.stdout.write('用户需要输入用户名和密码登录')
            self.stdout.write('✓ 更改已立即生效，无需重启服务')
            
        else:
            self.stdout.write('请指定操作:')
            self.stdout.write('  --disable  禁用登录（热切换）')
            self.stdout.write('  --enable   启用登录（热切换）')
            self.stdout.write('  --status   查看状态')

    def show_status(self):
        env_file = '.env'
        disable_login = self.read_env_value(env_file, 'DISABLE_LOGIN', 'False')
        auto_login_user = self.read_env_value(env_file, 'AUTO_LOGIN_USER', 'admin')
        
        self.stdout.write('=== 当前登录配置 ===')
        if disable_login.lower() == 'true':
            self.stdout.write(f'状态: ✗ 登录已禁用')
            self.stdout.write(f'自动登录用户: {auto_login_user}')
        else:
            self.stdout.write(f'状态: ✓ 登录已启用')
            self.stdout.write('用户需要输入用户名和密码')
        
        self.stdout.write('')
        self.stdout.write('管理命令:')
        self.stdout.write('  python manage.py toggle_login --disable  # 禁用登录')
        self.stdout.write('  python manage.py toggle_login --enable   # 启用登录')

    def read_env_value(self, env_file, key, default=''):
        """从.env文件读取值"""
        if not os.path.exists(env_file):
            return default
            
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith(f'{key}='):
                    return line.split('=', 1)[1]
        return default

    def update_env_file(self, env_file, key, value):
        """更新.env文件中的值"""
        lines = []
        key_found = False
        
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                lines = f.readlines()
        
        # 更新现有的key或添加新的key
        for i, line in enumerate(lines):
            if line.strip().startswith(f'{key}='):
                lines[i] = f'{key}={value}\n'
                key_found = True
                break
        
        if not key_found:
            lines.append(f'{key}={value}\n')
        
        with open(env_file, 'w') as f:
            f.writelines(lines)
