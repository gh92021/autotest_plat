# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os, json
import logging
from loadtest.models import WorkerNode
from django.utils import timezone

@csrf_exempt
def worker_register(request):
    # 工作节点注册
    if request.method == 'POST':
        data = json.loads(request.body)
        worker, created = WorkerNode.objects.get_or_create(
            name=data.get('name'),
            defaults={
                'host': data.get('host'),
                'port': data.get('port', 5557),
                'status': 'online'
            }
        )
        
        if not created:
            worker.status = 'online'
            worker.last_active = timezone.now()
            worker.save()
        logging.info(f'工作节点注册成功: {worker.id}')
        return JsonResponse({'status': 'registered', 'worker_id': worker.id})

@csrf_exempt
def worker_remove(request):
    # 工作节点移除
    if request.method == 'POST':
        data = json.loads(request.body)
        worker = WorkerNode.objects.get(id=data.get('worker_id'))
        worker.delete()
        logging.info(f'工作节点移除: {worker.id}')
        return JsonResponse({'status': 'removed', 'worker_id': worker.id})

def worker_list(request):
    workers = WorkerNode.objects.all()
    return render(request, 'loadtest/worker_list.html', {'workers': workers})