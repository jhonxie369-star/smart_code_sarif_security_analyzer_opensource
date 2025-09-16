from django.urls import path
from . import views
from api.documentation_views import documentation_view

urlpatterns = [
    path('', views.index, name='index'),
    path('help/', views.help_page, name='help'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
    path('docs/', documentation_view, name='documentation'),
    path('finding/<int:pk>/ai_analyze/', views.ai_analyze_finding, name='ai_analyze_finding'),
    path('finding/<int:pk>/kill_ai_analyze/', views.kill_ai_analyze_finding, name='kill_ai_analyze_finding'),
    path('finding/<int:pk>/rate_ai/', views.rate_ai_analysis, name='rate_ai_analysis'),
    path('finding/<int:pk>/update_status/', views.update_finding_status, name='update_finding_status'),
    path('ai-quality-stats/', views.ai_quality_statistics, name='ai_quality_statistics'),
    path('ai-quality-export/', views.ai_quality_export, name='ai_quality_export'),
    path('finding/<int:pk>/', views.finding_detail, name='finding_detail'),
    path('project/<int:pk>/', views.project_detail, name='project_detail'),
    # CWE相关API
    path('api/cwe/<int:cwe_number>/', views.get_cwe_info, name='get_cwe_info'),
    path('api/cwe/search/', views.search_cwe, name='search_cwe'),
    path('api/cwe/categories/', views.get_cwe_categories, name='get_cwe_categories'),
]
