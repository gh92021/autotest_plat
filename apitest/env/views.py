# apitest/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apitest.models import Module, Env
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
import logging


# ==================== 环境管理 ====================
def env_list(request):
    envs = Env.objects.all().select_related('module')
    module_id = request.GET.get('module')
    if module_id:
        envs = envs.filter(module_id=module_id)
    name = request.GET.get('name')
    if name:
        envs = envs.filter(name__icontains=name)
    url = request.GET.get('url')
    if url:
        envs = envs.filter(base_url__icontains=url)

    paginator = Paginator(envs, settings.PAGE_SIZE)
    page = request.GET.get('page', 1)
    try:
        envs = paginator.get_page(page)
    except PageNotAnInteger:
        envs = paginator.get_page(1)
    except EmptyPage:
        envs = paginator.get_page(paginator.num_pages)

    modules = Module.objects.all().order_by('name')
    return render(request, 'apitest/env_list.html', {'envs': envs, 'modules': modules})

def env_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        module_id = request.POST.get('module')
        base_url = request.POST.get('base_url')
        
        if Env.objects.filter(name=name).exists():
            messages.error(request, f'环境名称 "{name}" 已存在，请使用其他名称')
            return render(request, 'apitest/env_form.html', {
                'name': name,
                'description': description,
                'module_id': module_id,
                'base_url': base_url,
            })
        
        try:
            env = Env.objects.create(name=name, description=description, module_id=module_id, base_url=base_url)
            logging.info(f'环境 "{env.id}" 创建成功')
            messages.success(request, '环境创建成功')
            return redirect('apitest:env_list')
        except Exception as e:
            messages.error(request, f'创建环境失败: {str(e)}')
            return render(request, 'apitest/env_form.html', {
                'name': name,
                'description': description,
            })
    
    modules = Module.objects.all()
    return render(request, 'apitest/env_form.html', {'modules': modules})

def env_edit(request, pk):
    env = get_object_or_404(Env, pk=pk)
    env_id = pk
    
    if request.method == 'POST':
        env.name = request.POST.get('name')
        env.description = request.POST.get('description')
        env.base_url = request.POST.get('base_url')

        if Env.objects.filter(name=env.name).exclude(id=env_id).exists():
            messages.error(request, f'环境名称 "{env.name}" 已存在，请使用其他名称')
            return render(request, 'apitest/env_form.html', {
                'name': env.name,
                'description': env.description,
                'base_url': env.base_url,
            })
        
        try:
            env.save()
            logging.info(f'环境 "{env.id}" 更新成功')
            messages.success(request, '环境更新成功')
            return redirect('apitest:env_list')
        except Exception as e:
            messages.error(request, f'更新环境失败: {str(e)}')
            return render(request, 'apitest/env_form.html', {
                'name': env.name,
                'description': env.description,
                'base_url': env.base_url,
            })
    
    return render(request, 'apitest/env_form.html', {'env': env})

def env_delete(request, pk):
    if request.method == 'POST':
        env = get_object_or_404(Env, pk=pk)
        env.delete()
        logging.info(f'环境 "{pk}" 删除成功')
        messages.success(request, '环境删除成功')
        return redirect('apitest:env_list')
