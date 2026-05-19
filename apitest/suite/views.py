# apitest/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
import json, time
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.conf import settings
from apitest.models import TestCase, Project, TestExecution, TestSuite, SuiteCase, Parameters, Globals
from apitest.testcase.test_runner import TestRunner
from apitest.utils.run_api import get_request_data
import logging
import threading


# ==================== 测试计划管理 ====================
def suite_list(request):
    suites = TestSuite.objects.filter(deleted=0).select_related('project')
    project_id = request.GET.get('project')
    if project_id:
        suites = suites.filter(project_id=project_id)
    name = request.GET.get('name')
    if name:
        suites = suites.filter(name__icontains=name)
    
    paginator = Paginator(suites, settings.PAGE_SIZE)
    page = request.GET.get('page', 1)
    try:
        suites = paginator.page(page)
    except PageNotAnInteger:
        suites = paginator.page(1)
    except EmptyPage:
        suites = paginator.page(paginator.num_pages)

    projects = Project.objects.filter(deleted=0).order_by('name')
    return render(request, 'apitest/suite_list.html', {
        'suites': suites,
        'projects': projects
    })

def suite_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        project_id = request.POST.get('project')
        description = request.POST.get('description')
        
        suite = TestSuite.objects.create(
            name=name,
            project_id=project_id,
            description=description
        )
        logging.info(f'创建测试计划: {suite.id}')
        
        testcase_ids = request.POST.getlist('testcases')
        for order, tc_id in enumerate(testcase_ids):
            sc = SuiteCase.objects.create(
                suite=suite,
                testcase_id=tc_id,
                order=order
            )
            logging.info(f'测试计划关联用例: {sc.id}')
        
        messages.success(request, f'测试计划 "{name}" 创建成功')
        return redirect('apitest:suite_list')
    
    projects = Project.objects.filter(deleted=0)
    return render(request, 'apitest/suite_form.html', {
        'projects': projects,
    })

def suite_edit(request, pk):
    suite = get_object_or_404(TestSuite, pk=pk)
    
    if request.method == 'POST':
        suite.name = request.POST.get('name')
        suite.description = request.POST.get('description')
        suite.save()
        logging.info(f'更新测试计划: {suite.id}')
        
        suite.suitecase_set.all().delete()
        testcase_ids = request.POST.getlist('testcases')
        for order, tc_id in enumerate(testcase_ids):
            sc = SuiteCase.objects.create(
                suite=suite,
                testcase_id=tc_id,
                order=order
            )
            logging.info(f'测试计划关联用例: {sc.id}')
        
        messages.success(request, '测试计划更新成功')
        return redirect('apitest:suite_list')
    projects = Project.objects.filter(deleted=0)
    selected_ids = suite.testcases.values_list('id', flat=True)
    
    return render(request, 'apitest/suite_form.html', {
        'suite': suite,
        'projects': projects,
        'selected_ids': list(selected_ids)
    })

def suite_delete(request, pk):
    if request.method == 'POST':
        suite = get_object_or_404(TestSuite, pk=pk)
        suite_cases = SuiteCase.objects.filter(suite=suite)
        for sc in suite_cases:
            sc.delete()
        suite.deleted = 1
        suite.save()

        #suite.delete()
        logging.info(f'删除测试计划: {suite.id}')
        messages.success(request, '测试计划删除成功')
        return redirect('apitest:suite_list')


def run_suite(request, pk):
    logging.info(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}, 触发执行测试计划：{pk}")
    suite = get_object_or_404(TestSuite, pk=pk)
    
    execution = TestExecution.objects.create(
        name=f"执行测试计划: {suite.name}",
        execution_type='suite',
        target_id=pk,
        status='pending'
    )
    logging.info(f"创建执行计划成功：{execution.id}")
    
    testcases = []
    try:
        globals = Globals.objects.all()
        for i,sc in enumerate(suite.suitecase_set.all().select_related('testcase')):
            tc = sc.testcase
            if not tc.is_active:
                continue

            locals = tc.vars.filter(is_parametrize=False).first()
            if locals:
                locals = locals.var_value
            locals = json.loads(locals) if locals else {}
            parametrize = tc.vars.filter(is_parametrize=True).first()
            if parametrize:
                parametrize = parametrize.var_value

            steps = tc.steps.all()
            testcases.append({
                    'test_id': tc.id,
                    'name': tc.name,
                    'priority': tc.priority,
                    'teardown_script': tc.teardown_script,
                    'parametrize': parametrize if parametrize else None,
                    'steps': []
                })
            
            for step in steps:
                api = step.api
                if not api:
                    break
                env = api.env
                if not env:
                    break
                
                stp_data = get_request_data(api, env, step, locals, globals)
                step_data = {
                    'name': step.name,
                    'url': stp_data['url'],
                    'method': stp_data['method'],
                    'headers': stp_data['headers'],
                    'params': stp_data['params'],
                    'body': stp_data['body'],
                    'pre_script': step.pre_script,
                    'post_script': step.post_script,
                    'assertions': step.assertions
                }
                testcases[i]['steps'].append(step_data)
            logging.info(f"添加测试用例：{tc.name}")

        test_data = {'testcases': testcases}
        thread = threading.Thread(
            target=run_async,
            args=(execution, test_data),
            daemon=True
        )
        thread.start()

    except Exception as e:
        logging.error(f"{str(e)}")
        execution.status = 'failed'
        execution.error_message = str(e)
        execution.completed_at = timezone.now()
        execution.save()
    return redirect('apitest:execute_result', execution.id)

def run_async(execution, test_data):
    try:
        execution.status = 'running'
        execution.save()
        logging.info(f"runner执行开始: {execution.id}")
        runner = TestRunner(execution.id, test_data)
        pytest_result = runner.run_suite()
        logging.info(f"runner执行完成")

        execution = get_object_or_404(TestExecution, pk=execution.id)
        execution.status = pytest_result['status']
        execution.report_file = pytest_result.get('report_file', '')
        execution.total_tests = pytest_result.get('total_tests', 0)
        execution.passed_tests = pytest_result.get('passed_tests', 0)
        execution.failed_tests = pytest_result.get('failed_tests', 0)
        execution.error_message = pytest_result.get('error_message', '')
        execution.completed_at = timezone.now()
        execution.save()
        logging.info(f"执行状态更新完成")
        
    except Exception as e:
        logging.error(f"执行失败: {str(e)}")
        try:
            execution = get_object_or_404(TestExecution, pk=execution.id)
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.completed_at = timezone.now()
            execution.save()
        except Exception as ex:
            logging.error(f"更新执行记录失败: {str(ex)}")


def get_testcases(request):
    project_id = request.GET.get('project')
    testcases = []
    
    if project_id:
        testcases = TestCase.objects.filter(project_id=project_id, deleted=0, is_active=True).values('id', 'name', 'project__name')
        testcases = [
            {
                'id': tc['id'],
                'name': tc['name'],
                'project_name': tc['project__name']
            }
            for tc in testcases
        ]
    return JsonResponse(testcases, safe=False)

