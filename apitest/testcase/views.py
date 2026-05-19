# apitest/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
import json, time
from django.contrib import messages
from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from django.conf import settings
from apitest.models import Api, TestCase, SuiteCase, Steps, Project, TestExecution, Parameters, Globals
from apitest.utils.run_api import run_api, get_request_data
from apitest.utils.replace_vars import fill_parametrize
from apitest.utils.handle_vars import get_var, get_all_vars, set_var, clear_all_vars
from apitest.testcase.test_runner import TestRunner
import logging


# ==================== 测试用例管理 ====================
def testcase_list(request):
    testcases = TestCase.objects.filter(deleted=0).select_related('project')
    project_id = request.GET.get('project')
    if project_id:
        testcases = testcases.filter(project_id=project_id)
    name = request.GET.get('name')
    if name:
        testcases = testcases.filter(name__icontains=name)
    priority = request.GET.get('priority')
    if priority:
        testcases = testcases.filter(priority=priority)
    is_active = request.GET.get('is_active')
    if is_active is not None and is_active != '':
        testcases = testcases.filter(is_active=is_active)

    paginator = Paginator(testcases, settings.PAGE_SIZE)
    page = request.GET.get('page', 1)
    try:
        testcases = paginator.page(page)
    except PageNotAnInteger:
        testcases = paginator.page(1)
    except EmptyPage:
        testcases = paginator.page(paginator.num_pages)
    
    projects = Project.objects.filter(deleted=0).order_by('name')
    return render(request, 'apitest/tc_list.html', {
        'testcases': testcases,
        'projects': projects
    })

def testcase_create(request):
    if request.method == 'POST':
        try:
            testcase = TestCase.objects.create(
                name=request.POST.get('name'),
                priority=request.POST.get('priority'),
                project_id=request.POST.get('project'),
                teardown_script=request.POST.get('teardown_script', ''),
            )
            logging.info(f'创建测试用例: {testcase.id}')
            
            local_vars = request.POST.get('locals', '')
            if local_vars:
                Parameters.objects.create(
                    testcase=testcase,
                    var_name='local_vars',
                    var_value=local_vars,
                )
            parametrize_vars = request.POST.get('parametrize', '')
            if parametrize_vars:
                Parameters.objects.create(
                    testcase=testcase,
                    var_name='parametrize_vars',
                    var_value=parametrize_vars,
                    is_parametrize=True,
                )
            
            step_count = 0
            while True:
                api_input = request.POST.get(f'api_{step_count}')
                if not api_input:
                    break                
                api_id = None
                api_id = request.POST.get(f'api_id_{step_count}')
                if not api_id:
                    pass
                
                if api_id:
                    step = Steps.objects.create(
                        testcase=testcase,
                        api_id=api_id,
                        name=request.POST.get(f'name_{step_count}', ''),
                        replace_params=request.POST.get(f'replace_query_{step_count}', ''),
                        replace_body=request.POST.get(f'replace_body_{step_count}', ''),
                        pre_script=request.POST.get(f'pre_script_{step_count}', ''),
                        post_script=request.POST.get(f'post_script_{step_count}', ''),
                        assertions=request.POST.get(f'assertions_{step_count}', ''),
                    )
                
                step_count += 1
                logging.info(f'创建步骤: {step.id}')
            messages.success(request, f'测试用例 "{testcase.name}" 创建成功')
            return redirect('apitest:testcase_list')
        except Exception as e:
            messages.error(request, f'创建失败: {str(e)}')
    
    projects = Project.objects.filter(deleted=0)
    return render(request, 'apitest/tc_form.html', {'projects': projects})

def testcase_edit(request, pk):
    testcase = get_object_or_404(TestCase, pk=pk)
    steps = testcase.steps.all()
    locals = testcase.vars.filter(is_parametrize=False).first()
    parametrize = testcase.vars.filter(is_parametrize=True).first()
    
    if request.method == 'POST':
        testcase.name = request.POST.get('name')
        testcase.priority = request.POST.get('priority')
        testcase.project_id = request.POST.get('project')
        testcase.teardown_script = request.POST.get('teardown_script', '')
        testcase.save()
        logging.info(f'更新测试用例: {testcase.id}')

        testcase.vars.all().delete()
        local_vars = request.POST.get('locals', '')
        if local_vars:
            Parameters.objects.create(
                testcase=testcase,
                var_name='local_vars',
                var_value=local_vars,
            )
        parametrize_vars = request.POST.get('parametrize', '')
        if parametrize_vars:
            Parameters.objects.create(
                testcase=testcase,
                var_name='parametrize_vars',
                var_value=parametrize_vars,
                is_parametrize=True,
            )

        testcase.steps.all().delete()
        step_count = 0
        while True:
            api_input = request.POST.get(f'api_{step_count}')
            if not api_input:
                break
            
            api_id = request.POST.get(f'api_id_{step_count}')
            if api_id:
                step = Steps.objects.create(
                    testcase=testcase,
                    api_id=api_id,
                    name=request.POST.get(f'name_{step_count}', ''),
                    replace_params=request.POST.get(f'replace_query_{step_count}', ''),
                    replace_body=request.POST.get(f'replace_body_{step_count}', ''),
                    pre_script=request.POST.get(f'pre_script_{step_count}', ''),
                    post_script=request.POST.get(f'post_script_{step_count}', ''),
                    assertions=request.POST.get(f'assertions_{step_count}', ''),
                )
                logging.info(f'更新步骤: {step.id}')
            
            step_count += 1
        messages.success(request, '测试用例更新成功')
        return redirect('apitest:testcase_list')
    
    projects = Project.objects.filter(deleted=0)
    return render(request, 'apitest/tc_form.html', {
        'testcase': testcase,
        'projects': projects,
        'steps': steps,
        'locals': locals,
        'parametrize': parametrize,
    })

def testcase_delete(request, pk):
    if request.method == 'POST':
        testcase = get_object_or_404(TestCase, pk=pk)
        suitecases = SuiteCase.objects.filter(testcase=testcase)
        for sc in suitecases:
            sc.delete()
        testcase.deleted = 1
        testcase.save()

        #testcase.delete()
        logging.info(f'删除测试用例: {testcase.id}')
        messages.success(request, '测试用例删除成功')
        return redirect('apitest:testcase_list')

def testcase_active(request, pk):
    if request.method == 'POST':
        testcase = get_object_or_404(TestCase, pk=pk)
        status = testcase.is_active
        if status:
            testcase.is_active = False
            messages.success(request, '测试用例已禁用')
        else:
            testcase.is_active = True
            messages.success(request, '测试用例已启用')
        testcase.save()
        logging.info(f'更新测试用例状态: {testcase.id}')
        return redirect('apitest:testcase_list')

def testcase_copy(request, pk):
    original = get_object_or_404(TestCase, pk=pk)
    
    new_case = TestCase.objects.create(
        name=f"{original.name} (副本)",
        priority=original.priority,
        project=original.project,
        teardown_script=original.teardown_script,
        is_active=original.is_active
    )
    logging.info(f'复制测试用例: {new_case.id}')
    
    for var in original.vars.all():
        new_var = Parameters.objects.create(
            testcase=new_case,
            var_name=var.var_name,
            var_value=var.var_value,
            is_parametrize=var.is_parametrize,
        )

    for step in original.steps.all():
        new_step = Steps.objects.create(
            testcase=new_case,
            api_id=step.api_id,
            name=step.name,
            replace_params=step.replace_params,
            replace_body=step.replace_body,
            pre_script=step.pre_script,
            post_script=step.post_script,
            assertions=step.assertions,
        )
        logging.info(f'复制步骤: {new_step.id}')
    
    messages.success(request, f'已复制为: {new_case.name}')
    return redirect('apitest:testcase_list')

def testcase_detail(request, pk):
    testcase = get_object_or_404(TestCase, pk=pk)
    steps = testcase.steps.all()
    tc_data = {
        'testcase': testcase,
        'locals': testcase.vars.filter(is_parametrize=False).first(),
        'parametrize': testcase.vars.filter(is_parametrize=True).first(),
        'steps': steps,
    }
    return render(request, 'apitest/tc_detail.html', tc_data)

# ==================== 测试用例执行 ====================
def run_step(request, pk):
    if request.method == 'POST':
        try:
            global_var = Globals.objects.all()
            step = get_object_or_404(Steps, pk=pk)
            locals = step.testcase.vars.filter(is_parametrize=False).first()
            if locals:
                locals = locals.var_value
            #parametrize = step.testcase.vars.filter(is_parametrize=True).first().var_value
            api = step.api

            if not api:
                return JsonResponse({
                    'success': False,
                    'step_pass': False,
                    'error': '接口不存在'
                })
            env = api.env
            if not env:
                return JsonResponse({
                    'success': False,
                    'step_pass': False,
                    'error': '环境不存在'
                })
            step_pass = True

            _context_vars = {}
            pre_result = None
            if step.pre_script:
                try:
                    logging.info(f'执行前置脚本: \n{step.pre_script}')
                    exec(step.pre_script, globals(), _context_vars)
                    pre_result = '前置脚本执行成功'
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'step_pass': False,
                        'error': f'前置脚本执行失败: {str(e)}'
                    })
            
            locals = json.loads(locals) if locals else {}
            locals.update(_context_vars)
            tc_data = get_request_data(api, env, step, locals=locals, globals=global_var)
            try:
                response = run_api(tc_data)
            except Exception as e:
                return JsonResponse({
                    'success': True,
                    'pre_result': pre_result,
                    'request': tc_data,
                    'step_pass': False,
                    'response': f'接口请求失败: {str(e)}'
                })
    
            result = {
                'success': True,
                'request': {
                    'url': tc_data['url'],
                    'method': tc_data['method'],
                    'headers': tc_data['headers'],
                    'params': tc_data['params'],
                    'body': tc_data['body'],
                },
                'response': {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'content': response.text,
                    'json': response.json() if response.headers.get('content-type', '').startswith('application/json') else None,
                }
            }
            
            post_result = None
            if step.post_script:
                try:
                    logging.info(f'执行后置脚本: \n{step.post_script}')
                    exec(step.post_script, globals(), {'response': response})
                    post_result = '后置脚本执行成功'
                except Exception as e:
                    return JsonResponse({
                        'success': True,
                        'pre_result': pre_result,
                        'post_result': f'后置脚本执行失败: {str(e)}',
                        'response': result['response'],
                        'request': result['request'],
                        'step_pass': False,
                    })

            assertions = []
            all_passed = True
            
            try:
                response = response
                if step.assertions:
                    assertion_lines = step.assertions.strip().split('\n')
                    for line in assertion_lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            exec(line, globals(), {'response': response})
                            assertions.append({
                                'assertion': line,
                                'passed': True
                            })
                        except Exception as e:
                            all_passed = False
                            step_pass = False
                            assertions.append({
                                'assertion': line,
                                'passed': False,
                                'error': str(e)
                            })
                else:
                    assert response.status_code >= 200 and response.status_code < 300, f"接口状态码 {response.status_code}"
                    result['asserted'] = True
                    assertions.append({
                        'assertion': f"响应状态码 {response.status_code}",
                        'passed': True
                    })

            except Exception as e:
                all_passed = False
                step_pass = False
                if not step.assertions:
                    assertions.append({
                        'assertion': f"响应状态码",
                        'passed': False,
                        'error': str(e)
                    })
                else:
                    assertions.append({
                        'assertion': "断言执行错误",
                        'passed': False,
                        'error': str(e)
                    })

            result['assertions'] = assertions
            result['asserted'] = all_passed
            result['pre_result'] = pre_result
            result['post_result'] = post_result
            result['step_pass'] = step_pass
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'step_pass': False,
                'error': str(e)
            })
        # finally:
        #     clear_all_vars()
    
    return JsonResponse({'success': False, 'error': '只支持POST请求'})

def run_testcase(request, pk):    
    if request.method == 'POST':
        try:
            logging.info(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}, 触发执行用例：{pk}")
            testcase = get_object_or_404(TestCase, pk=pk)
            steps = testcase.steps.all()

            globals = Globals.objects.all()
            locals = testcase.vars.filter(is_parametrize=False).first()
            if locals:
                locals = locals.var_value
            locals = json.loads(locals) if locals else {}
            
            parametrize = testcase.vars.filter(is_parametrize=True).first()
            if parametrize:
                parametrize = parametrize.var_value
            
            test_data = {
                'testcases': [{
                    'name': testcase.name,
                    'priority': testcase.priority,
                    'parametrize': parametrize if parametrize else None,
                    'steps': [],
                    'teardown_script': testcase.teardown_script
                }]
            }
            
            for step in steps:
                api = step.api
                if not api:
                    return JsonResponse({
                        'success': False,
                        'error': f'{step.name} 的接口不存在'
                    })
                env = api.env
                if not env:
                    return JsonResponse({
                        'success': False,
                        'error': f'{api.name} 接口环境不存在'
                    })
                
                stp_data = get_request_data(api, env, step, locals=locals, globals=globals)
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
                test_data['testcases'][0]['steps'].append(step_data)
            
            execution = TestExecution.objects.create(
                name=f"执行用例: {testcase.name}",
                execution_type='case',
                target_id=pk,
                status='running'
            )
            logging.info(f"创建执行计划成功：{execution.id}")
            logging.info(f"用例数据：{test_data}")
            
            runner = TestRunner(execution.id, test_data)
            pytest_result = runner.run()
            logging.info(f"runner执行完成")
            
            results = pytest_result.get('execution_results', [])
            execution.status = pytest_result.get('status')
            execution.report_file = pytest_result.get('report_file', '')
            execution.total_tests = pytest_result.get('total_tests', 0)
            execution.passed_tests = pytest_result.get('passed_tests', 0)
            execution.failed_tests = pytest_result.get('failed_tests', 0)
            execution.error_message = pytest_result.get('error_message', '')
            execution.completed_at = timezone.now()
            execution.save()
            
            return JsonResponse({
                'success': True,
                'results': results,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': '只支持POST请求'})



def api_search(request):
    search_text = request.GET.get('search', '')
    
    apis = Api.objects.all()
    
    if search_text:
        apis = apis.filter(
            Q(name__icontains=search_text) | 
            Q(url__icontains=search_text)
        )
    
    api_list = []
    for api in apis:
        api_list.append({
            'id': api.id,
            'name': api.name,
            'url': api.url,
            'method': api.method
        })
    
    return JsonResponse({'apis': api_list})
