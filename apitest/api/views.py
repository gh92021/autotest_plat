# apitest/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.conf import settings
from apitest.models import Module, Env, Api
from apitest.utils.run_api import run_api
from apitest.utils.parse_curl import parse_curl_data
import logging


# ==================== 接口管理 ====================
def api_list(request):
    apis = Api.objects.all().select_related('module')
    module_id = request.GET.get('module')
    if module_id:
        apis = apis.filter(module_id=module_id)
    name = request.GET.get('name')
    if name:
        apis = apis.filter(name__icontains=name)
    url = request.GET.get('url')
    if url:
        apis = apis.filter(url__icontains=url)
    
    paginator = Paginator(apis, settings.PAGE_SIZE)
    page = request.GET.get('page', 1)
    try:
        apis = paginator.get_page(page)
    except PageNotAnInteger:
        apis = paginator.get_page(1)
    except EmptyPage:
        apis = paginator.get_page(paginator.num_pages)
    
    modules = Module.objects.all().order_by('name')
    return render(request, 'apitest/api_list.html', {
        'apis': apis,
        'modules': modules
    })

def api_create(request):
    envs = Env.objects.all()
    modules = Module.objects.all()
    all_envs = [{'id': env.id, 'name': env.name, 'module_id': env.module_id} for env in envs] 
    all_envs_json = json.dumps(all_envs, cls=DjangoJSONEncoder)

    if request.method == 'POST':
        try:
            api = Api.objects.create(
                name=request.POST.get('name'),
                module_id=request.POST.get('module'),
                env_id=request.POST.get('env'),
                url=request.POST.get('url'),
                method=request.POST.get('method'),
                headers=request.POST.get('headers', '{}'),
                params=request.POST.get('params', '{}'),
                body=request.POST.get('body', '{}'),
            )
            logging.info(f'创建接口: {api.id}')
            messages.success(request, f'接口 "{api.name}" 创建成功')
            return redirect('apitest:api_list')
        except Exception as e:
            messages.error(request, f'创建失败: {str(e)}')
    
    return render(request, 'apitest/api_form.html', {'modules': modules, 'envs': envs, 'all_envs_json': all_envs_json})

def api_edit(request, pk):
    api = get_object_or_404(Api, pk=pk)
    module_id = api.module_id
    
    if request.method == 'POST':
        api.name = request.POST.get('name')
        api.env_id = request.POST.get('env')
        api.url = request.POST.get('url')
        api.method = request.POST.get('method')
        api.headers = request.POST.get('headers', '{}')
        api.params = request.POST.get('params', '{}')
        api.body = request.POST.get('body', '{}')

        api.save()
        logging.info(f'更新接口: {api.id}')
        messages.success(request, '接口更新成功')
        return redirect('apitest:api_list')
    
    envs = Env.objects.filter(module_id=module_id)
    return render(request, 'apitest/api_form.html', {
        'api': api,
        'envs': envs,
    })

def api_delete(request, pk):
    if request.method == 'POST':
        api = get_object_or_404(Api, pk=pk)
        api.delete()
        logging.info(f'删除接口: {pk}')
        messages.success(request, '接口删除成功')
        return redirect('apitest:api_list')


# ==================== 运行接口 ====================
def api_detail(request, pk):
    api = get_object_or_404(Api, pk=pk)
    envs = Env.objects.all()
    module_id = api.module_id
    envs = envs.filter(module_id=module_id)

    selected_env_id = request.GET.get('env_id')
    if not selected_env_id:
        selected_env_id = api.env_id
    try:
        selected_env_id = int(selected_env_id)
    except (ValueError, TypeError):
        selected_env_id = api.env_id
    
    try:
        cur_env = Env.objects.get(pk=selected_env_id, module_id=module_id)
    except Env.DoesNotExist:
        cur_env = api.env
    api_data = {
        'api': api,
        'envs': envs,
        'selected_env_id': selected_env_id,
        'cur_env': cur_env,
    }
    return render(request, 'apitest/api_detail.html', api_data)

def execute_api(request, pk):
    if request.method == 'POST':
        try:
            api = get_object_or_404(Api, pk=pk)
            env_id = request.POST.get('env_id')
            if env_id:
                env = get_object_or_404(Env, pk=env_id)
            else:
                env = api.env

            url = env.base_url.rstrip('/') + '/' + api.url.lstrip('/')
            headers = api.headers if api.headers else {}
            params = api.params if api.params else {}
            body = api.body if api.body else {}
            
            api_data = {
                    'url': url,
                    'method': api.method,
                    'headers': headers,
                    'params': params,
                    'body': body,
                }
            response = run_api(api_data)
            logging.info(f'运行接口: {api.id},requests返回数据')
    
            result = {
                'success': True,
                'request': {
                    'url': url,
                    'method': api.method,
                    'headers': headers,
                    'params': params,
                    'body': body,
                },
                'response': {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'content': response.text,
                    'json': response.json() if response.headers.get('content-type', '').startswith('application/json') else None,
                }
            }
            
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': '只支持POST请求'})

def parse_curl(request):
    if request.method == 'POST':
        curl = request.POST.get('curl')
        if curl:
            try:
                data = parse_curl_data(curl)
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
            return JsonResponse(data)
        else:
            return JsonResponse({'success': False, 'error': 'curl参数不能为空'})