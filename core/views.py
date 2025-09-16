from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
import json
import subprocess
import re
from .models import Department, Project, ScanTask, Finding, SeverityManager
from .cwe_utils import CWEExplainer
from .authorization.decorators import smart_login_required, require_permission
from .authorization.roles_permissions import Permissions
from django.utils import timezone

def auto_login_view(request):
    """自动登录视图"""
    if getattr(settings, 'DISABLE_LOGIN', False):
        # 如果用户已经登录，直接重定向
        if request.user.is_authenticated:
            next_url = request.GET.get('next', '/admin/')
            return HttpResponseRedirect(next_url)
        
        # 自动登录用户
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
            except Exception as e:
                # 如果创建失败，返回错误信息
                return JsonResponse({
                    'error': f'无法创建用户: {str(e)}',
                    'message': '请手动创建admin用户或启用正常登录'
                }, status=500)
        
        # 登录成功后重定向
        next_url = request.GET.get('next', '/admin/')
        return HttpResponseRedirect(next_url)
    
    # 如果启用了登录，显示正常的登录表单
    # 这里我们需要调用Django原始的登录视图
    from django.contrib.admin.sites import site
    return site.login(request)

@smart_login_required
def index(request):
    """首页视图"""
    # 如果是API请求，返回JSON
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'message': '智能代码安全分析平台',
            'version': '1.0.0',
            'admin_url': '/admin/',
            'api_url': '/api/',
            'dashboard_url': '/dashboard/',
            'login_disabled': getattr(settings, 'DISABLE_LOGIN', False)
        })
    
    # 否则渲染HTML页面
    return render(request, 'index.html', {
        'login_disabled': getattr(settings, 'DISABLE_LOGIN', False)
    })

@smart_login_required
def help_page(request):
    """使用说明页面"""
    return render(request, 'help.html')

@require_permission(Permissions.STATISTICS_VIEW)
def dashboard(request):
    """统计看板主页"""
    departments = Department.objects.all()
    return render(request, 'core/dashboard.html', {'departments': departments})

@login_required
def dashboard_stats(request):
    """获取统计数据API"""
    department_filter = request.GET.get('department')
    
    # 基础查询
    findings_query = Finding.objects.select_related('project', 'project__department')
    projects_query = Project.objects.select_related('department')
    
    if department_filter:
        findings_query = findings_query.filter(project__department__name=department_filter)
        projects_query = projects_query.filter(department__name=department_filter)
    
    # 总体统计
    total_findings = findings_query.count()
    active_findings = findings_query.filter(active=True).count()
    
    # 严重程度统计 - 三级分级
    severity_stats = {}
    for severity, _ in SeverityManager.SEVERITY_CHOICES:
        count = findings_query.filter(severity=severity, active=True).count()
        severity_stats[severity] = count
    
    # 项目统计
    projects_data = []
    for project in projects_query:
        project_findings = findings_query.filter(project=project)
        active_count = project_findings.filter(active=True).count()
        
        # 计算最高严重程度
        max_severity = '低危'
        for severity, _ in reversed(SeverityManager.SEVERITY_CHOICES):
            if project_findings.filter(severity=severity, active=True).exists():
                max_severity = severity
                break
        
        # 各严重程度统计
        project_severity_stats = {}
        for severity, _ in SeverityManager.SEVERITY_CHOICES:
            count = project_findings.filter(severity=severity, active=True).count()
            project_severity_stats[severity] = count
        
        projects_data.append({
            'name': project.name,
            'department': project.department.name,
            'total_issues': active_count,
            'max_severity': max_severity,
            'stats': project_severity_stats,
            'business_criticality': project.business_criticality
        })
    
    # 按问题数量排序
    projects_data.sort(key=lambda x: x['total_issues'], reverse=True)
    
    # 趋势数据（最近30天）
    trend_data = []
    for i in range(30):
        date = timezone.now().date() - timedelta(days=i)
        count = findings_query.filter(date=date).count()
        trend_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    trend_data.reverse()
    
    # 高危漏洞分类统计（按CWE）- 只显示高危漏洞
    cwe_stats = {}
    high_risk_findings = findings_query.filter(active=True, severity='高危', cwe__isnull=False)
    cwe_findings = high_risk_findings.values('cwe').annotate(count=Count('cwe'))
    for item in cwe_findings:
        cwe_num = item['cwe']
        cwe_info = CWEExplainer.get_cwe_info(cwe_num)
        cwe_stats[f"CWE-{cwe_num}"] = {
            'count': item['count'],
            'name': cwe_info['name'] if cwe_info else f'CWE-{cwe_num}',
            'category': cwe_info['category'] if cwe_info else '其他'
        }
    
    # 状态统计
    status_stats = {
        'active': findings_query.filter(active=True).count(),
        'verified': findings_query.filter(verified=True).count(),
        'false_positive': findings_query.filter(false_p=True).count(),
        'mitigated': findings_query.filter(is_mitigated=True).count(),
        'risk_accepted': findings_query.filter(risk_accepted=True).count(),
    }
    
    return JsonResponse({
        'department': department_filter or 'all',
        'metrics': {
            'total_findings': total_findings,
            'active_findings': active_findings,
            'severity': severity_stats,
            'status': status_stats
        },
        'charts': {
            'severity': severity_stats,
            'categories': cwe_stats,
            'trend': trend_data,
            'projects': projects_data
        },
        'projects': projects_data
    })

@csrf_exempt
@require_http_methods(["POST"])
def ai_analyze_finding(request, pk):
    """AI分析单个漏洞 - 按照原工具设计"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '只支持POST请求'})
        
    try:
        finding = get_object_or_404(Finding, pk=pk)
        
        # 检查单个漏洞是否正在分析
        if finding.ai_analyzing:
            return JsonResponse({
                'success': False,
                'error': 'AI分析正在进行中，请稍后再试'
            })
        
        # 检查全局并发限制（最多10个同时AI分析）
        current_analyzing = Finding.objects.filter(ai_analyzing=True).count()
        if current_analyzing >= 10:
            return JsonResponse({
                'success': False,
                'error': f'当前有{current_analyzing}个AI分析任务正在进行，请稍后再试'
            })
        
        # 检查是否强制重新分析
        force_reanalyze = request.POST.get('force', 'false').lower() == 'true'
        
        # 如果已有分析结果且不是强制重新分析，直接返回缓存结果
        if (finding.ai_analysis and 
            finding.ai_analysis.get('risk_analysis') and 
            not force_reanalyze):
            return JsonResponse({
                'success': True,
                'analysis': finding.ai_analysis,
                'message': '使用缓存的分析结果'
            })
        
        # 设置分析状态
        finding.ai_analyzing = True
        finding.save(update_fields=['ai_analyzing'])
        
        try:
            # 进行AI分析
            analysis_result = _analyze_single_finding(finding)
            
            if analysis_result and not analysis_result.startswith('分析失败'):
                # 解析AI分析结果
                parsed_analysis = _parse_ai_analysis(analysis_result)
                parsed_analysis['cached_at'] = datetime.now().isoformat()
                
                # 保存分析结果
                finding.ai_analysis = parsed_analysis
                finding.ai_cached = True
                finding.ai_analyzing = False
                finding.save(update_fields=['ai_analysis', 'ai_cached', 'ai_analyzing'])
                
                return JsonResponse({
                    'success': True,
                    'analysis': parsed_analysis,
                    'message': 'AI分析完成' if not force_reanalyze else 'AI重新分析完成'
                })
            else:
                finding.ai_analyzing = False
                finding.save(update_fields=['ai_analyzing'])
                return JsonResponse({
                    'success': False,
                    'error': analysis_result or '分析失败'
                })
        except Exception as e:
            finding.ai_analyzing = False
            finding.save(update_fields=['ai_analyzing'])
            raise e
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'分析过程中发生错误: {str(e)}'
        })

def _analyze_single_finding(finding):
    """分析单个漏洞 - 模仿原工具的AI分析逻辑"""
    try:
        # 构建分析提示词
        source_context_text = ""
        has_long_lines = False
        if finding.source_context and finding.source_context.get('lines'):
            source_context_text = "\n- 源码上下文:"
            lines = finding.source_context['lines'][:10]  # 最多10行
            
            for line in lines:
                marker = ">>> " if line.get('is_target') else "    "
                content = line.get('content', '')
                
                # 处理超长行（如压缩的JS/CSS）
                if len(content) > 200:
                    has_long_lines = True
                    if line.get('is_target'):
                        # 目标行：显示前100字符 + 省略号 + 后100字符
                        content = content[:100] + " ... [压缩代码已截断] ... " + content[-100:]
                    else:
                        # 非目标行：只显示前100字符
                        content = content[:100] + " ... [行过长已截断]"
                
                source_context_text += f"\n  {marker}{line.get('number', '?'):4d}: {content}"
            
            if len(finding.source_context['lines']) > 10:
                source_context_text += "\n  ... (更多代码已省略)"
            
            # 添加超长行警告
            if has_long_lines:
                source_context_text += "\n\n⚠️ 注意：检测到源码包含超长行（可能为压缩代码），AI仅分析截取的关键内容，分析结果可能不够全面。建议查看完整源码进行人工审查。"
        
        prompt = f"""请分析以下代码安全问题，用中文提供简洁的解决方案。

规则ID: {finding.title}
问题详情:
- 文件: {finding.file_path}
- 行号: {finding.line_number}
- 描述: {finding.translated_message or finding.message}
- 严重程度: {finding.severity}{source_context_text}

必须严格按以下格式回答：

## 1. 安全风险分析
说明这个漏洞的危害和影响。

## 2. 具体修复方案
提供针对性的修复建议和代码示例。

```语言名
// 修复后的代码
// 请提供完整的修复代码
```

## 3. 防范建议
提供项目级别的防范措施。

重要要求：
- 所有代码必须使用 ```语言 代码``` 格式（如java/javascript/python等）
- 不要使用单独的语言标识
- 回答简洁明了，不要冗余内容
- 仅提供建议，无需工具操作"""
        
        # 调用Amazon Q
        result = subprocess.run(
            ['q', 'chat', prompt, '--no-interactive', '--trust-tools='],
            capture_output=True,
            text=True,
            timeout=90
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return _clean_ai_output(result.stdout)
        else:
            error_msg = result.stderr.strip() if result.stderr else '未知错误'
            return f"分析失败: {error_msg}"
            
    except subprocess.TimeoutExpired:
        return "分析超时，请稍后重试"
    except FileNotFoundError:
        return "Amazon Q未安装或不可用"
    except Exception as e:
        return f"错误: {str(e)}"

def _clean_ai_output(text):
    """清理AI输出"""
    # 移除ANSI颜色代码
    text = re.sub(r'\x1b\[[0-9;]*m', '', text)
    # 移除开头的 > 符号和空格
    text = re.sub(r'^[>\s]*', '', text, flags=re.MULTILINE)
    return text.strip()

def _parse_ai_analysis(analysis_text):
    """解析AI分析结果为结构化数据"""
    sections = {
        'risk_analysis': '',
        'solution': '',
        'prevention': '',
        'code_example': ''
    }
    
    current_section = None
    lines = analysis_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if '## 1. 安全风险分析' in line:
            current_section = 'risk_analysis'
        elif '## 2. 具体修复方案' in line:
            current_section = 'solution'
        elif '## 3. 防范建议' in line:
            current_section = 'prevention'
        elif line.startswith('##'):
            current_section = None
        elif current_section and line:
            if sections[current_section]:
                sections[current_section] += '\n' + line
            else:
                sections[current_section] = line
    
    return sections

@login_required
def finding_detail(request, pk):
    """漏洞详情页面"""
    finding = Finding.objects.select_related('project', 'scan_task').get(pk=pk)
    return render(request, 'core/finding_detail.html', {'finding': finding})

@login_required
def project_detail(request, pk):
    """项目详情页面"""
    project = Project.objects.select_related('department').get(pk=pk)
    findings = Finding.objects.filter(project=project).select_related('scan_task')
    
    # 统计信息
    stats = {
        'total': findings.count(),
        'active': findings.filter(active=True).count(),
        'critical': findings.filter(severity='Critical', active=True).count(),
        'high': findings.filter(severity='High', active=True).count(),
        'medium': findings.filter(severity='Medium', active=True).count(),
        'low': findings.filter(severity='Low', active=True).count(),
        'info': findings.filter(severity='Info', active=True).count(),
    }
    
    return render(request, 'core/project_detail.html', {
        'project': project,
        'findings': findings,
        'stats': stats
    })


@login_required
def get_cwe_info(request, cwe_number):
    """获取CWE详细信息API"""
    try:
        cwe_info = CWEExplainer.get_cwe_info(int(cwe_number))
        if cwe_info:
            return JsonResponse({
                'success': True,
                'cwe_info': cwe_info
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'CWE信息未找到'
            })
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': '无效的CWE编号'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def search_cwe(request):
    """搜索CWE API"""
    keyword = request.GET.get('q', '').strip()
    if not keyword:
        return JsonResponse({
            'success': False,
            'error': '请提供搜索关键词'
        })
    
    try:
        results = CWEExplainer.search_cwe(keyword)
        return JsonResponse({
            'success': True,
            'results': results
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def get_cwe_categories(request):
    """获取CWE分类API"""
    try:
        categories = CWEExplainer.get_all_categories()
        category_data = {}
        for category in categories:
            cwes = CWEExplainer.get_category_cwes(category)
            category_data[category] = cwes
        
        return JsonResponse({
            'success': True,
            'categories': category_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def update_finding_status(request, pk):
    """更新漏洞状态 - 单选模式"""
    try:
        finding = get_object_or_404(Finding, pk=pk)
        status_key = request.POST.get('status_key')
        
        if not status_key:
            return JsonResponse({'success': False, 'error': '缺少状态参数'})
        
        # 重置所有状态为False
        finding.active = False
        finding.verified = False
        finding.false_p = False
        finding.duplicate = False
        finding.out_of_scope = False
        finding.risk_accepted = False
        finding.under_review = False
        finding.is_mitigated = False
        
        # 设置选中的状态为True
        if hasattr(finding, status_key):
            setattr(finding, status_key, True)
            finding.save()
            return JsonResponse({'success': True, 'message': '状态更新成功'})
        else:
            return JsonResponse({'success': False, 'error': '无效的状态参数'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
def kill_ai_analyze_finding(request, pk):
    """终止AI分析"""
    try:
        finding = get_object_or_404(Finding, pk=pk)
        finding.ai_analyzing = False
        finding.save(update_fields=['ai_analyzing'])
        return JsonResponse({'success': True, 'message': 'AI分析已终止'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_http_methods(["POST"])
@smart_login_required
def rate_ai_analysis(request, pk):
    """AI分析质量评估"""
    try:
        finding = get_object_or_404(Finding, pk=pk)
        
        # 获取评估参数
        quality_rating = request.POST.get('quality_rating')
        quality_comment = request.POST.get('quality_comment', '')
        
        # 验证评估等级
        valid_ratings = ['excellent', 'good', 'poor']
        if quality_rating not in valid_ratings:
            return JsonResponse({
                'success': False,
                'error': '无效的评估等级'
            })
        
        # 保存评估结果
        finding.ai_quality_rating = quality_rating
        finding.ai_quality_comment = quality_comment
        finding.ai_rated_by = request.user
        finding.ai_rated_at = timezone.now()
        finding.save(update_fields=[
            'ai_quality_rating', 
            'ai_quality_comment', 
            'ai_rated_by', 
            'ai_rated_at'
        ])
        
        # 返回成功响应
        rating_text = {
            'excellent': '完整正确，可以直接用',
            'good': '建议正确，但是不能直接用', 
            'poor': '建议错误'
        }
        
        return JsonResponse({
            'success': True,
            'message': f'AI分析质量已评估为：{rating_text[quality_rating]}',
            'rating': quality_rating,
            'rating_text': rating_text[quality_rating],
            'comment': quality_comment,
            'rated_by': request.user.username,
            'rated_at': finding.ai_rated_at.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'评估失败: {str(e)}'
        })


@smart_login_required
def ai_quality_statistics(request):
    """AI分析质量统计页面"""
    from django.db.models import Count, Q
    
    # 获取统计数据
    total_analyzed = Finding.objects.filter(
        ai_analysis__isnull=False,
        ai_analysis__ne={}
    ).count()
    
    total_rated = Finding.objects.exclude(ai_quality_rating='').count()
    
    # 按质量等级统计
    quality_stats = Finding.objects.exclude(ai_quality_rating='').values(
        'ai_quality_rating'
    ).annotate(count=Count('id'))
    
    # 转换为字典
    quality_distribution = {}
    rating_labels = {
        'excellent': '完整正确，可以直接用',
        'good': '建议正确，但是不能直接用',
        'poor': '建议错误'
    }
    
    for stat in quality_stats:
        rating = stat['ai_quality_rating']
        quality_distribution[rating] = {
            'count': stat['count'],
            'label': rating_labels.get(rating, rating),
            'percentage': round(stat['count'] / total_rated * 100, 1) if total_rated > 0 else 0
        }
    
    # 最近的评估记录
    recent_ratings = Finding.objects.exclude(
        ai_quality_rating=''
    ).select_related('ai_rated_by', 'project').order_by('-ai_rated_at')[:10]
    
    context = {
        'total_analyzed': total_analyzed,
        'total_rated': total_rated,
        'rating_coverage': round(total_rated / total_analyzed * 100, 1) if total_analyzed > 0 else 0,
        'quality_distribution': quality_distribution,
        'recent_ratings': recent_ratings,
        'rating_labels': rating_labels,
    }
    
    return render(request, 'ai_quality_statistics.html', context)


@smart_login_required
def ai_quality_export(request):
    """导出AI质量评估数据"""
    import csv
    from django.http import HttpResponse
    
    # 创建CSV响应
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="ai_quality_report.csv"'
    
    # 添加BOM以支持Excel中文显示
    response.write('\ufeff')
    
    writer = csv.writer(response)
    
    # 写入表头
    writer.writerow([
        '漏洞ID', '项目名称', '漏洞标题', '严重程度', 
        'AI分析质量', '质量评估', '评估备注', '评估人', '评估时间'
    ])
    
    # 查询数据
    findings = Finding.objects.exclude(
        ai_quality_rating=''
    ).select_related('project', 'ai_rated_by').order_by('-ai_rated_at')
    
    rating_labels = {
        'excellent': '完整正确，可以直接用',
        'good': '建议正确，但是不能直接用',
        'poor': '建议错误'
    }
    
    # 写入数据
    for finding in findings:
        writer.writerow([
            finding.id,
            finding.project.name if finding.project else '',
            finding.title,
            finding.severity,
            finding.ai_quality_rating,
            rating_labels.get(finding.ai_quality_rating, ''),
            finding.ai_quality_comment,
            finding.ai_rated_by.username if finding.ai_rated_by else '',
            finding.ai_rated_at.strftime('%Y-%m-%d %H:%M:%S') if finding.ai_rated_at else ''
        ])
    
    return response