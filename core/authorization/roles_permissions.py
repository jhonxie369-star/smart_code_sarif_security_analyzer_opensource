"""
基于 DefectDojo 设计的角色权限系统
"""
from enum import IntEnum


class Roles(IntEnum):
    """用户角色定义"""
    VIEWER = 1      # 查看者 - 只读权限
    ANALYST = 2     # 分析师 - 可以分析漏洞，添加备注
    DEVELOPER = 3   # 开发者 - 可以修改漏洞状态，执行扫描
    MANAGER = 4     # 管理者 - 可以管理项目和用户
    ADMIN = 5       # 管理员 - 全部权限

    @classmethod
    def has_value(cls, value):
        try:
            Roles(value)
        except ValueError:
            return False
        return True

    @classmethod
    def get_choices(cls):
        return [
            (cls.VIEWER, '查看者'),
            (cls.ANALYST, '分析师'),
            (cls.DEVELOPER, '开发者'),
            (cls.MANAGER, '管理者'),
            (cls.ADMIN, '管理员'),
        ]


class Permissions(IntEnum):
    """权限定义"""
    
    # 部门权限 (1000-1099)
    DEPARTMENT_VIEW = 1001
    DEPARTMENT_ADD = 1002
    DEPARTMENT_EDIT = 1003
    DEPARTMENT_DELETE = 1004
    DEPARTMENT_MANAGE_MEMBERS = 1005
    
    # 项目权限 (1100-1199)
    PROJECT_VIEW = 1101
    PROJECT_ADD = 1102
    PROJECT_EDIT = 1103
    PROJECT_DELETE = 1104
    PROJECT_MANAGE_MEMBERS = 1105
    PROJECT_SCAN = 1106
    
    # 扫描任务权限 (1200-1299)
    SCAN_VIEW = 1201
    SCAN_ADD = 1202
    SCAN_EDIT = 1203
    SCAN_DELETE = 1204
    SCAN_KILL = 1205
    
    # 漏洞权限 (1300-1399)
    FINDING_VIEW = 1301
    FINDING_ADD = 1302
    FINDING_EDIT = 1303
    FINDING_DELETE = 1304
    FINDING_UPDATE_STATUS = 1305
    FINDING_AI_ANALYZE = 1306
    FINDING_TRANSLATE = 1307
    
    # 备注权限 (1400-1499)
    NOTE_VIEW = 1401
    NOTE_ADD = 1402
    NOTE_EDIT = 1403
    NOTE_DELETE = 1404
    
    # 统计权限 (1500-1599)
    STATISTICS_VIEW = 1501
    STATISTICS_EXPORT = 1502
    
    # 系统权限 (1600-1699)
    SYSTEM_SETTINGS = 1601
    USER_MANAGEMENT = 1602
    SYSTEM_LOGS = 1603

    @classmethod
    def get_department_permissions(cls):
        """获取部门相关权限"""
        return [
            cls.DEPARTMENT_VIEW,
            cls.DEPARTMENT_ADD,
            cls.DEPARTMENT_EDIT,
            cls.DEPARTMENT_DELETE,
            cls.DEPARTMENT_MANAGE_MEMBERS,
        ]
    
    @classmethod
    def get_project_permissions(cls):
        """获取项目相关权限"""
        return [
            cls.PROJECT_VIEW,
            cls.PROJECT_ADD,
            cls.PROJECT_EDIT,
            cls.PROJECT_DELETE,
            cls.PROJECT_MANAGE_MEMBERS,
            cls.PROJECT_SCAN,
        ]
    
    @classmethod
    def get_finding_permissions(cls):
        """获取漏洞相关权限"""
        return [
            cls.FINDING_VIEW,
            cls.FINDING_ADD,
            cls.FINDING_EDIT,
            cls.FINDING_DELETE,
            cls.FINDING_UPDATE_STATUS,
            cls.FINDING_AI_ANALYZE,
            cls.FINDING_TRANSLATE,
        ]


# 角色权限映射
ROLE_PERMISSIONS = {
    Roles.VIEWER: [
        # 查看者只有查看权限
        Permissions.DEPARTMENT_VIEW,
        Permissions.PROJECT_VIEW,
        Permissions.SCAN_VIEW,
        Permissions.FINDING_VIEW,
        Permissions.NOTE_VIEW,
        Permissions.STATISTICS_VIEW,
    ],
    
    Roles.ANALYST: [
        # 分析师在查看者基础上增加分析权限
        Permissions.DEPARTMENT_VIEW,
        Permissions.PROJECT_VIEW,
        Permissions.SCAN_VIEW,
        Permissions.FINDING_VIEW,
        Permissions.FINDING_AI_ANALYZE,
        Permissions.FINDING_TRANSLATE,
        Permissions.NOTE_VIEW,
        Permissions.NOTE_ADD,
        Permissions.NOTE_EDIT,
        Permissions.STATISTICS_VIEW,
    ],
    
    Roles.DEVELOPER: [
        # 开发者在分析师基础上增加修改权限
        Permissions.DEPARTMENT_VIEW,
        Permissions.PROJECT_VIEW,
        Permissions.PROJECT_SCAN,
        Permissions.SCAN_VIEW,
        Permissions.SCAN_ADD,
        Permissions.SCAN_KILL,
        Permissions.FINDING_VIEW,
        Permissions.FINDING_UPDATE_STATUS,
        Permissions.FINDING_AI_ANALYZE,
        Permissions.FINDING_TRANSLATE,
        Permissions.NOTE_VIEW,
        Permissions.NOTE_ADD,
        Permissions.NOTE_EDIT,
        Permissions.STATISTICS_VIEW,
    ],
    
    Roles.MANAGER: [
        # 管理者有大部分权限，除了系统级权限
        Permissions.DEPARTMENT_VIEW,
        Permissions.DEPARTMENT_ADD,
        Permissions.DEPARTMENT_EDIT,
        Permissions.PROJECT_VIEW,
        Permissions.PROJECT_ADD,
        Permissions.PROJECT_EDIT,
        Permissions.PROJECT_MANAGE_MEMBERS,
        Permissions.PROJECT_SCAN,
        Permissions.SCAN_VIEW,
        Permissions.SCAN_ADD,
        Permissions.SCAN_EDIT,
        Permissions.SCAN_KILL,
        Permissions.FINDING_VIEW,
        Permissions.FINDING_EDIT,
        Permissions.FINDING_UPDATE_STATUS,
        Permissions.FINDING_AI_ANALYZE,
        Permissions.FINDING_TRANSLATE,
        Permissions.NOTE_VIEW,
        Permissions.NOTE_ADD,
        Permissions.NOTE_EDIT,
        Permissions.NOTE_DELETE,
        Permissions.STATISTICS_VIEW,
        Permissions.STATISTICS_EXPORT,
    ],
    
    Roles.ADMIN: [
        # 管理员拥有所有权限
        permission for permission in Permissions
    ],
}


def role_has_permission(role_id, permission):
    """检查角色是否有指定权限"""
    try:
        role = Roles(role_id)
        return permission in ROLE_PERMISSIONS.get(role, [])
    except ValueError:
        return False


def get_user_permissions(user):
    """获取用户的所有权限"""
    if user.is_superuser:
        return list(Permissions)
    
    # 这里可以扩展为从数据库获取用户角色
    # 目前简化为根据用户状态判断
    if user.is_staff:
        return ROLE_PERMISSIONS.get(Roles.ADMIN, [])
    else:
        return ROLE_PERMISSIONS.get(Roles.VIEWER, [])