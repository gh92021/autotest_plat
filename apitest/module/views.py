# apitest/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apitest.models import Module
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging


# ==================== 服务管理 ====================
def module_list(request):
    modules = Module.objects.all()
    name = request.GET.get('name', '')
    if name:
        modules = modules.filter(name__icontains=name)
    paginator = Paginator(modules, settings.PAGE_SIZE)
    
    try:
        page = request.GET.get('page', 1)
        modules = paginator.page(page)
    except PageNotAnInteger:
        modules = paginator.page(1)
    except EmptyPage:
        modules = paginator.page(paginator.num_pages)
    return render(request, 'apitest/module_list.html', {'modules': modules})

def module_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        git_url = request.POST.get('git_url')
        
        if Module.objects.filter(name=name).exists():
            messages.error(request, f'服务名称 "{name}" 已存在，请使用其他名称')
            return render(request, 'apitest/module_form.html', {
                'name': name,
                'description': description,
                'git_url': git_url,
            })
        
        try:
            module = Module.objects.create(name=name, description=description, git_url=git_url)
            logging.info(f'创建服务: {module.id}')
            messages.success(request, '服务创建成功')
            return redirect('apitest:module_list')
        except Exception as e:
            messages.error(request, f'创建服务失败: {str(e)}')
            return render(request, 'apitest/module_form.html', {
                'name': name,
                'description': description,
                'git_url': git_url,
            })
    
    return render(request, 'apitest/module_form.html')

def module_edit(request, pk):
    module = get_object_or_404(Module, pk=pk)
    module_id = pk
    
    if request.method == 'POST':
        module.name = request.POST.get('name')
        module.description = request.POST.get('description')
        module.git_url = request.POST.get('git_url')

        if Module.objects.filter(name=module.name).exclude(id=module_id).exists():
            messages.error(request, f'服务名称 "{module.name}" 已存在，请使用其他名称')
            return render(request, 'apitest/module_form.html', {
                'name': module.name,
                'description': module.description,
                'git_url': module.git_url,
            })
        
        try:
            module.save()
            logging.info(f'更新服务: {module.id}')
            messages.success(request, '服务更新成功')
            return redirect('apitest:module_list')
        except Exception as e:
            messages.error(request, f'更新服务失败: {str(e)}')
            return render(request, 'apitest/module_form.html', {
                'name': module.name,
                'description': module.description,
                'git_url': module.git_url,
            })
    
    return render(request, 'apitest/module_form.html', {'module': module})

def module_delete(request, pk):
    if request.method == 'POST':
        module = get_object_or_404(Module, pk=pk)
        module.delete()
        logging.info(f'删除服务: {pk}')
        messages.success(request, '服务删除成功')
        return redirect('apitest:module_list')
