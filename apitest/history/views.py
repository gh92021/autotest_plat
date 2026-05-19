# apitest/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.conf import settings
from apitest.models import TestExecution
import logging


# ==================== 运行记录 ====================
def execute_result(request, pk):
    execution = get_object_or_404(TestExecution, pk=pk)
    return render(request, 'apitest/result.html', {'execution': execution})

def report_download(request, pk):
    execution = get_object_or_404(TestExecution, pk=pk)
    
    if execution.report_file:
        import os
        if os.path.exists(execution.report_file):
            name = os.path.basename(execution.report_file)
            logging.info(f'下载报告文件: {execution.report_file}')
            return FileResponse(
                open(execution.report_file, 'rb'),
                as_attachment=True,
                filename=f'report_{execution.id}.html' if name.endswith('.html') else f'report_{execution.id}.xml'
            )
    
    messages.error(request, '报告文件不存在')
    return redirect('apitest:execute_result', pk)

def run_history(request):
    executions = TestExecution.objects.all()

    exe_type = request.GET.get('type')
    if exe_type:
        executions = executions.filter(execution_type=exe_type)
    target_id = request.GET.get('target_id')
    if target_id:
        executions = executions.filter(target_id=target_id)
    status = request.GET.get('status')
    if status:
        executions = executions.filter(status=status)

    paginator = Paginator(executions, settings.PAGE_SIZE)
    page = request.GET.get('page', 1)
    try:
        executions = paginator.page(page)
    except PageNotAnInteger:
        executions = paginator.page(1)
    except EmptyPage:
        executions = paginator.page(paginator.num_pages)
    
    return render(request, 'apitest/run_history.html', {'executions': executions})
