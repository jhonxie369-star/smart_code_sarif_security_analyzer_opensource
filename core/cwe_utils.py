"""
CWE (Common Weakness Enumeration) 工具类
提供CWE编号的中文解释和分类信息
"""

import json
import os
from django.conf import settings

class CWEExplainer:
    """CWE解释器 - 提供常见CWE的中文解释"""
    
    _cwe_data = None
    _last_modified = None
    
    @classmethod
    def _load_cwe_data(cls):
        """加载CWE数据"""
        try:
            data_file = os.path.join(os.path.dirname(__file__), '..', 'cwe_chinese_data.json')
            current_modified = os.path.getmtime(data_file)
            
            # 检查文件是否更新
            if cls._cwe_data is None or cls._last_modified != current_modified:
                with open(data_file, 'r', encoding='utf-8') as f:
                    cls._cwe_data = json.load(f)
                cls._last_modified = current_modified
        except FileNotFoundError:
            # 如果文件不存在，使用默认数据
            if cls._cwe_data is None:
                cls._cwe_data = cls._get_default_cwe_data()
        return cls._cwe_data
    
    @classmethod
    def _get_default_cwe_data(cls):
        """获取默认CWE数据"""
        return {
        # 注入类漏洞
        79: {
            'name': '跨站脚本攻击 (XSS)',
            'description': '应用程序在发送给用户的网页中包含了未经验证的用户输入，可能导致恶意脚本在用户浏览器中执行',
            'category': '注入攻击',
            'severity_hint': 'Medium-High',
            'mitigation': '对用户输入进行适当的验证、编码和转义'
        },
        89: {
            'name': 'SQL注入',
            'description': '应用程序在构造SQL查询时使用了未经验证的用户输入，攻击者可能执行恶意SQL命令',
            'category': '注入攻击',
            'severity_hint': 'High-Critical',
            'mitigation': '使用参数化查询、存储过程或ORM框架'
        },
        78: {
            'name': '命令注入',
            'description': '应用程序执行包含用户输入的系统命令，可能导致任意命令执行',
            'category': '注入攻击',
            'severity_hint': 'High-Critical',
            'mitigation': '避免直接执行用户输入，使用白名单验证'
        },
        
        # 认证和授权
        287: {
            'name': '认证不当',
            'description': '系统无法正确验证用户身份，可能导致未授权访问',
            'category': '认证授权',
            'severity_hint': 'High',
            'mitigation': '实施强认证机制，使用多因素认证'
        },
        285: {
            'name': '授权不当',
            'description': '系统未能正确控制用户对资源的访问权限',
            'category': '认证授权',
            'severity_hint': 'High',
            'mitigation': '实施基于角色的访问控制(RBAC)'
        },
        
        # 加密问题
        327: {
            'name': '使用破损或危险的加密算法',
            'description': '使用了已知存在安全缺陷的加密算法',
            'category': '加密问题',
            'severity_hint': 'Medium-High',
            'mitigation': '使用现代安全的加密算法如AES、RSA'
        },
        326: {
            'name': '加密强度不足',
            'description': '使用的加密密钥长度不足以抵御现代攻击',
            'category': '加密问题',
            'severity_hint': 'Medium',
            'mitigation': '使用足够长度的密钥(如AES-256)'
        },
        
        # 输入验证
        20: {
            'name': '输入验证不当',
            'description': '应用程序未能正确验证输入数据的格式、类型或范围',
            'category': '输入验证',
            'severity_hint': 'Medium',
            'mitigation': '实施严格的输入验证和白名单过滤'
        },
        22: {
            'name': '路径遍历',
            'description': '攻击者可以通过特制的文件路径访问预期目录之外的文件',
            'category': '输入验证',
            'severity_hint': 'High',
            'mitigation': '验证和规范化文件路径，使用安全的文件操作API'
        },
        
        # 缓冲区错误
        120: {
            'name': '缓冲区溢出',
            'description': '程序向缓冲区写入的数据超过了其分配的空间',
            'category': '内存安全',
            'severity_hint': 'High-Critical',
            'mitigation': '使用安全的字符串函数，进行边界检查'
        },
        125: {
            'name': '缓冲区越界读取',
            'description': '程序读取超出缓冲区边界的内存',
            'category': '内存安全',
            'severity_hint': 'Medium-High',
            'mitigation': '进行适当的边界检查和输入验证'
        },
        
        # 信息泄露
        200: {
            'name': '信息暴露',
            'description': '系统向未授权用户暴露了敏感信息',
            'category': '信息泄露',
            'severity_hint': 'Medium',
            'mitigation': '限制错误信息的详细程度，实施适当的访问控制'
        },
        209: {
            'name': '通过错误消息的信息暴露',
            'description': '错误消息包含了可能被攻击者利用的敏感信息',
            'category': '信息泄露',
            'severity_hint': 'Low-Medium',
            'mitigation': '使用通用错误消息，记录详细错误到日志'
        },
        
        # 会话管理
        384: {
            'name': '会话固定',
            'description': '应用程序在用户认证前后使用相同的会话标识符',
            'category': '会话管理',
            'severity_hint': 'Medium',
            'mitigation': '在认证后重新生成会话ID'
        },
        
        # 配置问题
        16: {
            'name': '配置',
            'description': '软件配置存在安全问题',
            'category': '配置安全',
            'severity_hint': 'Medium',
            'mitigation': '遵循安全配置最佳实践'
        },
        
        # 竞态条件
        362: {
            'name': '竞态条件',
            'description': '程序的行为依赖于不可控制的事件时序',
            'category': '并发问题',
            'severity_hint': 'Medium-High',
            'mitigation': '使用适当的同步机制，避免共享资源竞争'
        },
        
        # 资源管理
        401: {
            'name': '资源未正确释放',
            'description': '程序未能正确释放已分配的资源',
            'category': '资源管理',
            'severity_hint': 'Low-Medium',
            'mitigation': '确保在所有代码路径中正确释放资源'
        },
        
        # 业务逻辑
        840: {
            'name': '业务逻辑错误',
            'description': '应用程序的业务逻辑存在缺陷',
            'category': '业务逻辑',
            'severity_hint': 'Medium',
            'mitigation': '仔细审查业务逻辑，进行充分测试'
        },
        
        # 服务端请求伪造
        918: {
            'name': '服务端请求伪造 (SSRF)',
            'description': '应用程序从用户控制的输入获取远程资源，未验证目标URL，攻击者可访问内网资源',
            'category': '注入攻击',
            'severity_hint': 'High',
            'mitigation': '验证和过滤URL，使用白名单限制可访问的域名和端口'
        },
        
        # 其他常见CWE
        352: {
            'name': '跨站请求伪造 (CSRF)',
            'description': '应用程序未验证请求来源，攻击者可诱导用户执行非预期操作',
            'category': '认证授权',
            'severity_hint': 'Medium-High',
            'mitigation': '使用CSRF令牌，验证Referer头，实施同源策略'
        },
        
        190: {
            'name': '整数溢出',
            'description': '算术运算结果超出数据类型能表示的范围，可能导致意外行为',
            'category': '内存安全',
            'severity_hint': 'Medium-High',
            'mitigation': '进行边界检查，使用安全的数学库'
        },
        
        117: {
            'name': '输出转义不当',
            'description': '输出数据时未进行适当的转义或编码，可能导致注入攻击',
            'category': '输入验证',
            'severity_hint': 'Medium-High',
            'mitigation': '对所有输出进行适当的HTML编码和转义'
        },
        
        476: {
            'name': '空指针解引用',
            'description': '程序试图访问空指针指向的内存位置',
            'category': '内存安全',
            'severity_hint': 'Medium',
            'mitigation': '在使用指针前进行空值检查'
        },
        
        798: {
            'name': '硬编码凭据',
            'description': '在源代码中硬编码密码、密钥等敏感信息',
            'category': '配置安全',
            'severity_hint': 'High',
            'mitigation': '使用配置文件或环境变量存储敏感信息'
        }
    }
    
    # CWE分类
    CATEGORIES = {
        '注入攻击': ['79', '89', '78', '918'],
        '认证授权': ['287', '285', '352'],
        '加密问题': ['327', '326'],
        '输入验证': ['20', '22', '117'],
        '内存安全': ['120', '125', '190', '476'],
        '信息泄露': ['200', '209'],
        '会话管理': ['384'],
        '配置安全': ['16', '798'],
        '并发问题': ['362'],
        '资源管理': ['401'],
        '业务逻辑': ['840']
    }
    
    @classmethod
    def get_cwe_info(cls, cwe_number):
        """获取CWE信息"""
        if not cwe_number:
            return None
            
        cwe_data = cls._load_cwe_data()
        cwe_info = cwe_data.get(str(cwe_number))
        if cwe_info:
            return {
                'cwe': cwe_number,
                'name': cwe_info['name'],
                'description': cwe_info['description'],
                'category': cwe_info['category'],
                'severity_hint': cwe_info['severity_hint'],
                'mitigation': cwe_info['mitigation'],
                'url': f'https://cwe.mitre.org/data/definitions/{cwe_number}.html'
            }
        else:
            # 未知CWE，返回基本信息
            return {
                'cwe': cwe_number,
                'name': f'CWE-{cwe_number}',
                'description': f'CWE-{cwe_number} 相关的安全弱点，请查阅官方文档了解详情',
                'category': '其他',
                'severity_hint': 'Unknown',
                'mitigation': '请参考CWE官方文档获取修复建议',
                'url': f'https://cwe.mitre.org/data/definitions/{cwe_number}.html'
            }
    
    @classmethod
    def get_category_cwes(cls, category):
        """获取分类下的所有CWE"""
        return cls.CATEGORIES.get(category, [])
    
    @classmethod
    def get_all_categories(cls):
        """获取所有分类"""
        return list(cls.CATEGORIES.keys())
    
    @classmethod
    def search_cwe(cls, keyword):
        """搜索CWE"""
        results = []
        keyword = keyword.lower()
        cwe_data = cls._load_cwe_data()
        
        for cwe_num, info in cwe_data.items():
            if (keyword in info['name'].lower() or 
                keyword in info['description'].lower() or
                keyword in info['category'].lower()):
                results.append({
                    'cwe': int(cwe_num),
                    'name': info['name'],
                    'category': info['category']
                })
        
        return results