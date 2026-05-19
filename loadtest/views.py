# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from loadtest.models import TestTask, TestScript, WorkerNode

running_tests = {}

# 首页
def index(request):
    tasks = TestTask.objects.all()
    data = {
        'total_scripts': TestScript.objects.count(),
        'total_tasks': TestTask.objects.count(),
        'running_tasks': TestTask.objects.filter(status='running').count(),
        'worker_count': WorkerNode.objects.count(),
        'recent_tasks': tasks[:10],
    }
    return render(request, 'loadtest/index.html', data)
