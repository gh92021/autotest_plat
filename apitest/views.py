# Create your views here.
# apitest/views.py
from django.shortcuts import render
from .models import Project, TestCase, TestSuite, TestExecution

# 首页
def index(request):
    projects = Project.objects.filter(deleted=0)
    testcases = TestCase.objects.filter(deleted=0)[:5]
    executions = TestExecution.objects.all()[:5]
    
    context = {
        'project_count': projects.count(),
        'testcase_count': TestCase.objects.filter(deleted=0).count(),
        'suite_count': TestSuite.objects.filter(deleted=0).count(),
        'recent_executions': executions,
        'recent_testcases': testcases,
    }
    return render(request, 'apitest/index.html', context)
