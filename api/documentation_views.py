from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.authorization.decorators import smart_login_required

@smart_login_required
def documentation_view(request):
    """开发文档视图"""
    return render(request, 'api/documentation.html')

@smart_login_required
def api_overview_view(request):
    """API概览视图"""
    return render(request, 'api/api_overview.html')

@smart_login_required
def api_docs_view(request):
    """API文档视图"""
    return render(request, 'api/api_docs.html')