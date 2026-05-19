# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os, json
import logging
from loadtest.models import TestScript
from loadtest.ai_service.ai_generator import AIGenerator


# ==================== 脚本管理 ====================
def script_list(request):
    scripts = TestScript.objects.all()
    return render(request, 'loadtest/script_list.html', {'scripts': scripts})


def script_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        scenario = request.POST.get('scenario')
        target_url = request.POST.get('target_url')
        api_curls = request.POST.get('api_curls')
        script_content = request.POST.get('script_content', '')
        testdata = request.POST.get('testdata', '{}')
        
        script = TestScript.objects.create(
            name=name,
            scenario=scenario,
            target_url=target_url,
            api_curls=api_curls,
            script_content=script_content,
            testdata=testdata,
        )
        logging.info(f'创建测试脚本: {script.id}')
        script_file = settings.LOCUST_SCRIPTS_DIR / f'script_{script.id}.py'
        script_file.parent.mkdir(parents=True, exist_ok=True)
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        messages.success(request, '测试脚本创建成功')
        return redirect('loadtest:script_list')
    
    return render(request, 'loadtest/script_create.html')

def script_edit(request, pk):
    script = get_object_or_404(TestScript, pk=pk)
    
    if request.method == 'POST':
        script.name = request.POST.get('name')
        script.scenario = request.POST.get('scenario')
        script.target_url = request.POST.get('target_url')
        script.api_curls = request.POST.get('api_curls')
        script.script_content = request.POST.get('script_content')
        script.testdata = request.POST.get('testdata', '{}')
        script.save()
        logging.info(f'更新测试脚本: {script.id}')
        
        script_file = settings.LOCUST_SCRIPTS_DIR / f'script_{script.id}.py'
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script.script_content)
        
        messages.success(request, '脚本更新成功')
        return redirect('loadtest:script_list')
    
    return render(request, 'loadtest/script_edit.html', {'script': script})

def script_delete(request, pk):
    script = get_object_or_404(TestScript, pk=pk)
    script.delete()
    logging.info(f'删除测试脚本: {pk}')
    
    script_file = settings.LOCUST_SCRIPTS_DIR / f'script_{pk}.py'
    if os.path.exists(script_file):
        os.remove(script_file)
    
    messages.success(request, '脚本删除成功')
    return redirect('loadtest:script_list')

def script_detail(request, pk):
    script = get_object_or_404(TestScript, pk=pk)
    return JsonResponse({'content': script.script_content})

def script_generate(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            scenario = data.get('scenario', '')
            api_curls = data.get('api_curls', '')
            
            if not scenario and not api_curls:
                return JsonResponse({'success': False, 'message': '请至少提供场景描述或CURL请求'})
            
            ai_gen = AIGenerator()
            script_content = ai_gen.gen_locust_script(scenario, api_curls)
            
            return JsonResponse({
                'success': True,
                'script_content': script_content
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    return JsonResponse({'success': False, 'message': '仅支持POST请求'})

def testdata_generate(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            api_curls = data.get('api_curls', '')
            if not api_curls:
                return JsonResponse({'success': False, 'message': '请提供CURL请求'})
            
            ai_gen = AIGenerator()
            testdata = ai_gen.gen_test_data(api_curls, 20)
            
            return JsonResponse({
                'success': True,
                'testdata': testdata
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    return JsonResponse({'success': False, 'message': '仅支持POST请求'})