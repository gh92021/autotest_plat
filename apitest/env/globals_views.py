# Create your views here.
# apitest/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from apitest.models import Globals
from django.conf import settings
import logging

# ==================== 全局参数设置 ====================
def globals_list(request):
    globals = Globals.objects.all()
    name = request.GET.get('name', '')
    if name:
        globals = globals.filter(name__icontains=name)
    paginator = Paginator(globals, settings.PAGE_SIZE)
    
    try:
        page = request.GET.get('page', 1)
        projects = paginator.page(page)
    except PageNotAnInteger:
        projects = paginator.page(1)
    except EmptyPage:
        projects = paginator.page(paginator.num_pages)
    return render(request, 'apitest/globals_list.html', {'globals': globals})

def globals_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        value = request.POST.get('value')
        description = request.POST.get('description')
        
        if Globals.objects.filter(name=name).exists():
            messages.error(request, f'全局参数名称 "{name}" 已存在，请使用其他名称')
            return render(request, 'apitest/globals_form.html', {
                'name': name,
                'value': value,
                'description': description,
            })
        
        try:
            globals = Globals.objects.create(name=name, value=value, description=description)
            logging.info(f'创建全局参数: {globals.id}')
            messages.success(request, '全局参数创建成功')
            return redirect('apitest:globals_list')
        except Exception as e:
            messages.error(request, f'创建全局参数失败: {str(e)}')
            return render(request, 'apitest/globals_form.html', {
                'name': name,
                'value': value,
                'description': description,
            })
    
    return render(request, 'apitest/globals_form.html')

def globals_edit(request, pk):
    globals = get_object_or_404(Globals, pk=pk)
    globals_id = pk
    
    if request.method == 'POST':
        globals.name = request.POST.get('name')
        globals.value = request.POST.get('value')
        globals.description = request.POST.get('description')

        if Globals.objects.filter(name=globals.name).exclude(id=globals_id).exists():
            messages.error(request, f'全局参数名称 "{globals.name}" 已存在，请使用其他名称')
            return render(request, 'apitest/globals_form.html', {
                'name': globals.name,
                'value': globals.value,
                'description': globals.description,
            })
        
        try:
            globals.save()
            logging.info(f'更新全局参数: {globals.id}')
            messages.success(request, '全局参数更新成功')
            return redirect('apitest:globals_list')
        except Exception as e:
            messages.error(request, f'更新全局参数失败: {str(e)}')
            return render(request, 'apitest/globals_form.html', {
                'name': globals.name,
                'value': globals.value,
                'description': globals.description,
            })
    
    return render(request, 'apitest/globals_form.html', {'globals': globals})

def globals_delete(request, pk):
    if request.method == 'POST':
        globals = get_object_or_404(Globals, pk=pk)
        globals.delete()
        logging.info(f'删除全局参数: {pk}')
        messages.success(request, '全局参数删除成功')
        return redirect('apitest:globals_list')
