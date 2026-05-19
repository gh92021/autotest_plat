# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
import os
from loadtest.models import TestTask, TestReport, TaskRecord


def report_download(request, pk):
    record = get_object_or_404(TaskRecord, pk=pk)
    
    try:
        report = TestReport.objects.get(record=record)
        if report.report_file:
            if os.path.exists(report.report_file):
                return FileResponse(
                    open(report.report_file, 'rb'), 
                    as_attachment=True
                )
    except:
        pass
    
    return JsonResponse({'error': '报告文件不存在'}, status=404)

def report_view(request, pk):
    record = get_object_or_404(TaskRecord, pk=pk)
    task = record.task
    try:
        report = TestReport.objects.get(record=record)
        return render(request, 'loadtest/report.html', {'record': record, 'report': report, 'task': task})
    except TestReport.DoesNotExist:
        messages.info(request, '报告尚未生成')
        return redirect('loadtest:task_detail', task.id)
