// 页面导航层级管理
const PAGE_HIERARCHY = {
    // 根页面
    '/': null,
    
    // 一级页面 - 从首页访问
    '/admin/': '/',
    '/api/': '/',
    
    // 二级页面 - 从管理后台访问
    '/api/quick-scan/': '/admin/',
    '/api/task-monitor/': '/admin/',
    '/api/error-logs/': '/admin/',
    '/api/overview/': '/admin/',
    '/admin/core/': '/admin/',
    '/admin/auth/': '/admin/',
    
    // 三级页面 - 从二级页面访问
    '/api/scan-logs/': '/api/task-monitor/',
    '/admin/core/project/': '/admin/',
    '/admin/core/finding/': '/admin/',
    '/admin/core/department/': '/admin/',
    '/admin/core/scantask/': '/admin/',
    '/admin/core/findingnote/': '/admin/',
    '/admin/core/statushistory/': '/admin/',
    '/admin/auth/user/': '/admin/',
    '/admin/auth/group/': '/admin/',
    
    // 四级页面 - 详情页面
    '/admin/core/project/add/': '/admin/core/project/',
    '/admin/core/finding/add/': '/admin/core/finding/',
    '/admin/core/department/add/': '/admin/core/department/',
    '/admin/core/scantask/add/': '/admin/core/scantask/',
    '/admin/auth/user/add/': '/admin/auth/user/',
    '/admin/auth/group/add/': '/admin/auth/group/',
};

function getParentPage(currentPath) {
    // 移除查询参数，只保留路径部分
    const pathOnly = currentPath.split('?')[0];
    
    // 精确匹配
    if (PAGE_HIERARCHY.hasOwnProperty(pathOnly)) {
        return PAGE_HIERARCHY[pathOnly];
    }
    
    // 处理带ID的详情页面（如 /admin/core/project/1/change/）
    const patterns = [
        { regex: /^\/admin\/core\/project\/\d+\/(change|delete)\/$/, parent: '/admin/core/project/' },
        { regex: /^\/admin\/core\/finding\/\d+\/(change|delete)\/$/, parent: '/admin/core/finding/' },
        { regex: /^\/admin\/core\/department\/\d+\/(change|delete)\/$/, parent: '/admin/core/department/' },
        { regex: /^\/admin\/core\/scantask\/\d+\/(change|delete)\/$/, parent: '/admin/core/scantask/' },
        { regex: /^\/admin\/auth\/user\/\d+\/(change|delete)\/$/, parent: '/admin/auth/user/' },
        { regex: /^\/admin\/auth\/group\/\d+\/(change|delete)\/$/, parent: '/admin/auth/group/' },
    ];
    
    for (const pattern of patterns) {
        if (pattern.regex.test(pathOnly)) {
            return pattern.parent;
        }
    }
    
    // 处理带查询参数的列表页面
    if (pathOnly === '/admin/core/finding/' && currentPath.includes('project__id__exact=')) {
        // 从项目页面进入的漏洞列表，返回项目列表
        return '/admin/core/project/';
    }
    
    if (pathOnly === '/admin/core/project/' && currentPath.includes('department__id__exact=')) {
        // 从部门筛选的项目列表，返回管理后台
        return '/admin/';
    }
    
    // 模糊匹配（按路径长度排序，优先匹配更具体的路径）
    const sortedPaths = Object.keys(PAGE_HIERARCHY).sort((a, b) => b.length - a.length);
    for (const path of sortedPaths) {
        if (pathOnly.startsWith(path) && pathOnly !== path) {
            return PAGE_HIERARCHY[path];
        }
    }
    
    // 默认返回首页
    return '/';
}

function smartBack() {
    const currentPath = window.location.pathname + window.location.search;
    const parentPage = getParentPage(currentPath);
    
    if (parentPage) {
        window.location.href = parentPage;
    } else {
        // 根页面或无法确定父页面时，尝试history.back()
        if (window.history.length > 1) {
            history.back();
        } else {
            window.location.href = '/admin/';
        }
    }
}

// 全局函数，供所有页面使用
window.smartBack = smartBack;