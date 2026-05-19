# testapp/urls.py
from django.urls import path
from . import views
from .project import views as project_views
from .module import views as module_views
from .env import views as env_views, globals_views
from .api import views as api_views
from .testcase import views as testcase_views
from .suite import views as suite_views
from .history import views as history_views

app_name = 'apitest'

urlpatterns = [
    # 首页
    path('', views.index, name='index'),
    
    # 项目管理
    path('projects/', project_views.project_list, name='project_list'),
    path('projects/create/', project_views.project_create, name='project_create'),
    path('projects/<int:pk>/edit/', project_views.project_edit, name='project_edit'),
    path('projects/<int:pk>/delete/', project_views.project_delete, name='project_delete'),
    
    # 服务管理
    path('modules/', module_views.module_list, name='module_list'),
    path('modules/create/', module_views.module_create, name='module_create'),
    path('modules/<int:pk>/edit/', module_views.module_edit, name='module_edit'),
    path('modules/<int:pk>/delete/', module_views.module_delete, name='module_delete'),
    
    # 环境管理
    path('envs/', env_views.env_list, name='env_list'),
    path('envs/create/', env_views.env_create, name='env_create'),
    path('envs/<int:pk>/edit/', env_views.env_edit, name='env_edit'),
    path('envs/<int:pk>/delete/', env_views.env_delete, name='env_delete'),
    
    # 全局参数管理
    path('globals/', globals_views.globals_list, name='globals_list'),
    path('globals/create/', globals_views.globals_create, name='globals_create'),
    path('globals/<int:pk>/edit/', globals_views.globals_edit, name='globals_edit'),
    path('globals/<int:pk>/delete/', globals_views.globals_delete, name='globals_delete'),
    
    # 接口管理
    path('apis/', api_views.api_list, name='api_list'),
    path('apis/create/', api_views.api_create, name='api_create'),
    path('apis/<int:pk>/edit/', api_views.api_edit, name='api_edit'),
    path('apis/<int:pk>/delete/', api_views.api_delete, name='api_delete'),
    path('apis/<int:pk>/detail/', api_views.api_detail, name='api_detail'),
    path('apis/<int:pk>/run/', api_views.execute_api, name='execute_api'),
    path('apis/parse-curl/', api_views.parse_curl, name='parse_curl'),

    # 搜索路由
    path('apis/api-list/', testcase_views.api_search, name='api_search'),
    path('testcases/tc-list/', suite_views.get_testcases, name='get_testcases'),

    # 测试用例管理
    path('testcases/', testcase_views.testcase_list, name='testcase_list'),
    path('testcases/create/', testcase_views.testcase_create, name='testcase_create'),
    path('testcases/<int:pk>/edit/', testcase_views.testcase_edit, name='testcase_edit'),
    path('testcases/<int:pk>/delete/', testcase_views.testcase_delete, name='testcase_delete'),
    path('testcases/<int:pk>/active/', testcase_views.testcase_active, name='testcase_active'),
    path('testcases/<int:pk>/copy/', testcase_views.testcase_copy, name='testcase_copy'),
    path('testcases/<int:pk>/detail/', testcase_views.testcase_detail, name='testcase_detail'),
    path('testcases/<int:pk>/run/', testcase_views.run_testcase, name='execute_testcase'),
    path('testcases/steps/<int:pk>/run/', testcase_views.run_step, name='run_step'),
    
    # 测试计划管理
    path('suites/', suite_views.suite_list, name='suite_list'),
    path('suites/create/', suite_views.suite_create, name='suite_create'),
    path('suites/<int:pk>/edit/', suite_views.suite_edit, name='suite_edit'),
    path('suites/<int:pk>/delete/', suite_views.suite_delete, name='suite_delete'),
    path('suites/<int:pk>/execute/', suite_views.run_suite, name='execute_suite'),
    
    # 执行结果
    path('execution/<int:pk>/', history_views.execute_result, name='execute_result'),
    path('execution/<int:pk>/download/', history_views.report_download, name='report_download'),
    path('executions/', history_views.run_history, name='run_history'),
]