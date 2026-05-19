# perfapp/urls.py
from django.urls import path
from . import views
from loadtest.view import scripts as script_views
from loadtest.view import tasks as task_views
from loadtest.view import reports as report_views
from loadtest.view import worker as worker_views

app_name = 'loadtest'

urlpatterns = [
    # 首页
    path('', views.index, name='index'),
    
    # 脚本管理
    path('scripts/', script_views.script_list, name='script_list'),
    path('scripts/create/', script_views.script_create, name='script_create'),
    path('scripts/<int:pk>/edit/', script_views.script_edit, name='script_edit'),
    path('scripts/<int:pk>/delete/', script_views.script_delete, name='script_delete'),
    path('scripts/<int:pk>/detail/', script_views.script_detail, name='script_detail'),
    
    # 任务管理
    path('tasks/', task_views.task_list, name='task_list'),
    path('tasks/create/', task_views.task_create, name='task_create'),
    path('tasks/<int:pk>/edit/', task_views.task_edit, name='task_edit'),
    path('tasks/<int:pk>/delete/', task_views.task_delete, name='task_delete'),
    path('tasks/<int:pk>/start/', task_views.task_start, name='task_start'),
    path('tasks/<int:pk>/stop/', task_views.task_stop, name='task_stop'),
    path('tasks/<int:pk>/', task_views.task_detail, name='task_detail'),
    path('tasks/record/<int:stamp>/', task_views.task_record_detail, name='task_record_detail'),
    
    # 报告
    path('reports/<int:pk>/report/', report_views.report_view, name='report_view'),
    path('reports/<int:pk>/download/', report_views.report_download, name='report_download'),
    
    # AI API
    path('api/ai/generate-script/', script_views.script_generate, name='script_generate'),
    path('api/ai/generate-data/', script_views.testdata_generate, name='testdata_generate'),

    # 工作节点
    path('workers/', worker_views.worker_list, name='worker_list'),
    path('workers/register/', worker_views.worker_register, name='worker_register'),
    path('workers/remove/', worker_views.worker_remove, name='worker_remove'),
]