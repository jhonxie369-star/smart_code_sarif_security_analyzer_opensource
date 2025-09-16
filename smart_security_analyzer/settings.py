import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载.env文件
def load_env_file(env_path):
    """手动加载.env文件"""
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

# 加载.env文件
load_env_file(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_extensions',
    'django_filters',
    
    # 自定义应用
    'core',
    'parsers',
    'ai_analysis',
    'translation',
    'statistics',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.AutoLoginMiddleware',  # 自动登录中间件
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smart_security_analyzer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'smart_security_analyzer.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'smart_security_analyzer_opensource'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 登录配置
DISABLE_LOGIN = os.getenv('DISABLE_LOGIN', 'False').lower() == 'true'
AUTO_LOGIN_USER = os.getenv('AUTO_LOGIN_USER', 'admin')

# 如果禁用登录，设置LOGIN_URL为None来绕过登录检查
if DISABLE_LOGIN:
    LOGIN_URL = None
    LOGIN_REDIRECT_URL = '/' #登录后进入根路径
    LOGOUT_REDIRECT_URL = '/admin/'
else:
    LOGIN_URL = '/admin/login/'
    LOGIN_REDIRECT_URL = '/'  # 登录后进入根路径
    LOGOUT_REDIRECT_URL = '/admin/login/'

# REST Framework settings - 支持可配置认证
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [] if DISABLE_LOGIN else [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ] if DISABLE_LOGIN else [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# 会话配置 - 优化用户体验
SESSION_COOKIE_AGE = 86400 * 7  # 7天
SESSION_SAVE_EVERY_REQUEST = True  # 每次请求都更新会话
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # 浏览器关闭后会话不过期
SESSION_COOKIE_HTTPONLY = True  # 安全性
SESSION_COOKIE_SECURE = False  # 开发环境设为False，生产环境应设为True
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF保护

# 记住我功能
REMEMBER_COOKIE_AGE = 86400 * 30  # 30天
REMEMBER_COOKIE_NAME = 'remember_token'

# 缓存配置 - 使用数据库缓存替代Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
    }
}

# 自定义配置
# 报告路径配置
REPORT_CONFIG = {
    'BASE_PATH': os.getenv('REPORT_BASE_PATH', str(BASE_DIR / 'workspace' / 'reports')),
    'PROJECT_PATH': os.getenv('PROJECT_BASE_PATH', str(BASE_DIR / 'workspace' / 'projects')),
    'STRUCTURE': '{department}/{project}',
    'SUPPORTED_FORMATS': ['sarif', 'json', 'xml'],
}

# AI分析配置
AI_CONFIG = {
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
    'OPENAI_MODEL': os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
    'CACHE_ENABLED': True,
    'TIMEOUT': 90,
}

# 翻译配置
TRANSLATION_CONFIG = {
    'ENABLED': True,
    'FROM_LANG': 'en',
    'TO_LANG': 'zh',
    'CACHE_ENABLED': True,
}

# 自动扫描配置
AUTO_SCAN_CONFIG = {
    'ENABLED': os.getenv('AUTO_SCAN_ENABLED', 'True').lower() == 'true',
    'WORK_DIR': os.getenv('SCAN_WORK_DIR', str(BASE_DIR / 'workspace' / 'scan_temp')),
    'OUTPUT_DIR': os.getenv('SCAN_OUTPUT_DIR', str(BASE_DIR / 'workspace' / 'reports')),
    'PROJECT_DIR': os.getenv('SCAN_PROJECT_DIR', str(BASE_DIR / 'workspace' / 'projects')),
    'TIMEOUT': int(os.getenv('SCAN_TIMEOUT', '3600')),
    'TOOLS': {
        'CODEQL_RULES': os.getenv('CODEQL_RULES', str(BASE_DIR / 'tools' / 'codeql-rules')),
        'CODEQL_BIN': os.getenv('CODEQL_BIN', str(BASE_DIR / 'tools' / 'codeql' / 'codeql')),
        'SEMGREP_BIN': os.getenv('SEMGREP_BIN', 'semgrep'),
        'JDK_HOME': os.getenv('JDK_HOME', str(BASE_DIR / 'tools' / 'jdk')),
    }
}

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'smart_security_analyzer': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# 确保日志目录存在
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
