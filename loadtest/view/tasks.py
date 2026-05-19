# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
import logging
import time
import json
import threading
from loadtest.models import TestScript, TestTask, TestReport, TaskRecord #, TestResult, WorkerNode
from loadtest.runner import LocustRunner
from loadtest.ai_service.ai_analyze import ResultAnalyzer


running_tasks = {}

# ==================== 测试任务管理 ====================
def task_list(request):
    tasks = TestTask.objects.all()
    return render(request, 'loadtest/task_list.html', {'tasks': tasks})

def task_detail(request, pk):
    task = get_object_or_404(TestTask, pk=pk)
    script = task.script
    records = TaskRecord.objects.filter(task=task)
    latest_stamp = records.first().task_stamp if records.exists() else None
    return render(request, 'loadtest/task_detail.html', {'task': task, 'script': script, 'records': records, 'latest_stamp': latest_stamp})

def task_create(request):
    if request.method == 'POST':
        script_id = request.POST.get('script')
        script = get_object_or_404(TestScript, pk=script_id)

        task = TestTask.objects.create(
            name=request.POST.get('name'),
            script=script,
            users=int(request.POST.get('users', 10)),
            spawn_rate=int(request.POST.get('spawn_rate', 1)),
            run_time=int(request.POST.get('run_time', 60)),
            mode=request.POST.get('mode', 'standalone'),
            master_host=request.POST.get('master_host', ''),
            master_port=int(request.POST.get('master_port', 5557)),
            worker_nodes=request.POST.get('worker_nodes', ''),
        )
        logging.info(f'创建测试任务: {task.id}')
        messages.success(request, f'测试任务 "{task.name}" 创建成功')
        return redirect('loadtest:task_list')
    
    scripts = TestScript.objects.all()
    return render(request, 'loadtest/task_form.html', {'scripts': scripts})

def task_edit(request, pk):
    task = get_object_or_404(TestTask, pk=pk)
    script = task.script
    
    if request.method == 'POST':
        script_id = request.POST.get('script')
        script = get_object_or_404(TestScript, pk=script_id)
        task.name = request.POST.get('name')
        task.users = int(request.POST.get('users', 10))
        task.spawn_rate = int(request.POST.get('spawn_rate', 1))
        task.run_time = int(request.POST.get('run_time', 60))
        task.mode = request.POST.get('mode', 'standalone')
        task.master_host=request.POST.get('master_host', '')
        task.master_port=int(request.POST.get('master_port', 5557))
        task.worker_nodes=request.POST.get('worker_nodes', '')
        task.script = script

        task.save()
        logging.info(f'更新测试任务: {task.id}')
        messages.success(request, '测试任务更新成功')
        return redirect('loadtest:task_list')
    
    scripts = TestScript.objects.all()
    return render(request, 'loadtest/task_form.html', {'task': task, 'script': script, 'scripts': scripts})

def task_delete(request, pk):
    task = get_object_or_404(TestTask, pk=pk)
    task.delete()
    logging.info(f'删除测试任务: {pk}')
    messages.success(request, '测试任务删除成功')
    return redirect('loadtest:task_list')

def task_start(request, pk):
    task = get_object_or_404(TestTask, pk=pk)
    if task.status == 'running':
        messages.error(request, '测试任务已在运行中')
        return redirect('loadtest:task_detail', task.id)
    
    stamp = int(time.time())
    runner = LocustRunner(task, stamp)
    record = TaskRecord.objects.create(task=task, task_stamp=stamp)
    
    def run_test():
        try:
            if task.mode == 'standalone':
                process = runner.run_standalone()
            else:
                process = runner.run_master()
                process_wk = []
                worker_nodes = json.loads(task.worker_nodes)
                for node in worker_nodes:
                    process_wk.append(runner.run_worker(task.master_host))
                logging.info(f'{task.id}: 工作节点 {process_wk}')
            
            if process is None:
                return
            
            # 启动监控线程
            running_tasks[task.id] = runner
            monitor_thread = threading.Thread(target=runner.monitor_stats)
            monitor_thread.daemon = True
            monitor_thread.start()
            logging.info(f'{task.id}: 监控线程启动')
            
            #process.wait()
            stdout, stderr = process.communicate()
            generate_report(task.id, stamp)
            
        except Exception as e:
            task.status = 'failed'
            task.save()
            logging.error(f"测试失败: {e}")

    thread = threading.Thread(target=run_test)
    thread.daemon = True
    thread.start()
    
    task.status = 'running'
    task.started_at = timezone.now()
    task.save()
    logging.info(f'{task.id}: status = running')
    
    messages.success(request, f'测试任务 "{task.name}" 已启动')
    return redirect('loadtest:task_detail', task.id)

def task_stop(request, pk):
    task = get_object_or_404(TestTask, pk=pk)
    
    if task.id in running_tasks:
        runner = running_tasks[task.id]
        runner.stop()
        del running_tasks[task.id]
    
    task.status = 'stopped'
    task.completed_at = timezone.now()
    task.save()
    logging.info(f'{task.id}: status = stopped')
    
    messages.success(request, '测试任务已停止')
    return redirect('loadtest:task_detail', task.id)

def generate_report(task_id, stamp):
    task = get_object_or_404(TestTask, pk=task_id)
    record = get_object_or_404(TaskRecord, task_stamp=stamp)
    results = task.results.filter(task_stamp=stamp)
    if not results:
        return
    
    response_times = []    
    for result in results:
        raw_data = result.raw_data
        for stat in raw_data.get('rows', []):
            response_times.append(float(stat.get('Total Average Response Time', 0)))
    response_times = list(filter(lambda x: x > 0, response_times))
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # 调用AI分析
    stats = results.first().raw_data
    analyzer = ResultAnalyzer()
    analysis = analyzer.analyze_report(task, stats)
    print(analysis)
    
    issues = analysis.get('issues', '')
    report = TestReport.objects.create(
        task=task,
        record=record,
        report_file=settings.REPORTS_DIR / f'test_{task_id}_{stamp}' / 'report.html',
        summary=analysis.get('summary', ''),
        issues='\n'.join(issues) if type(issues) == list else issues,
        suggestions='\n'.join(analysis.get('suggestions', [])),
    )
    
    task.status = 'completed'
    task.completed_at = timezone.now()
    record.total_requests = results.first().total_requests
    record.avg_response_time = avg_response_time
    record.rps = results.first().current_rps
    record.fail_ratio = results.first().cur_fail_ratio
    record.save()
    task.save()
    logging.info(f'{task.id}-{stamp}: 更新任务数据')

def task_record_detail(request, stamp):
    record = get_object_or_404(TaskRecord, task_stamp=stamp)
    task = record.task
    results = task.results.filter(task_stamp=stamp).order_by('timestamp')
    report = None
    if task.status == 'completed':
        report = get_object_or_404(TestReport, record=record)
    
    return render(request, 'loadtest/record_detail.html', {
        'task': task,
        'record': record,
        'results': results,
        'report': report
    })
