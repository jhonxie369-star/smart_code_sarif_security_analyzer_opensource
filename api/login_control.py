"""
登录控制API - 支持运行时热切换登录模式
"""
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@csrf_exempt
@require_http_methods(["GET", "POST"])
def login_control_api(request):
    """登录控制API端点"""
    
    if request.method == 'GET':
        # 获取当前登录状态
        status = get_login_status()
        return JsonResponse({
            'success': True,
            'data': status
        })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')  # 'enable' 或 'disable'
            
            if action == 'enable':
                result = enable_login()
            elif action == 'disable':
                result = disable_login()
            else:
                return JsonResponse({
                    'success': False,
                    'error': '无效的操作，请使用 enable 或 disable'
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'message': result['message'],
                'data': get_login_status()
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': '无效的JSON数据'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

def get_login_status():
    """获取当前登录状态"""
    env_file = '.env'
    disable_login = read_env_value(env_file, 'DISABLE_LOGIN', 'False')
    auto_login_user = read_env_value(env_file, 'AUTO_LOGIN_USER', 'admin')
    
    return {
        'login_disabled': disable_login.lower() == 'true',
        'auto_login_user': auto_login_user,
        'mode': '自动登录' if disable_login.lower() == 'true' else '正常登录',
        'hot_switch_supported': True
    }

def enable_login():
    """启用登录功能"""
    env_file = '.env'
    update_env_file(env_file, 'DISABLE_LOGIN', 'False')
    return {
        'message': '登录功能已启用（热切换），用户需要输入用户名和密码登录'
    }

def disable_login():
    """禁用登录功能"""
    env_file = '.env'
    update_env_file(env_file, 'DISABLE_LOGIN', 'True')
    return {
        'message': '登录功能已禁用（热切换），用户将自动以admin身份登录'
    }

def read_env_value(env_file, key, default=''):
    """从.env文件读取值"""
    if not os.path.exists(env_file):
        return default
        
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith(f'{key}='):
                return line.split('=', 1)[1]
    return default

def update_env_file(env_file, key, value):
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