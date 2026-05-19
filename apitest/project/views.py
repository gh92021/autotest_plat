# Create your views here.
# apitest/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from apitest.models import Project, TestSuite, SuiteCase
from django.conf import settings
import logging

# ==================== 项目管理 ====================
def project_list(request):
    projects = Project.objects.filter(deleted=0)
    name = request.GET.get('name', '')
    if name:
        projects = projects.filter(name__icontains=name)
    paginator = Paginator(projects, settings.PAGE_SIZE)
    
    try:
        page = request.GET.get('page', 1)
        projects = paginator.page(page)
    except PageNotAnInteger:
        projects = paginator.page(1)
    except EmptyPage:
        projects = paginator.page(paginator.num_pages)
    return render(request, 'apitest/project_list.html', {'projects': projects})

def project_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if Project.objects.filter(name=name).exists():
            messages.error(request, f'项目名称 "{name}" 已存在，请使用其他名称')
            return render(request, 'apitest/project_form.html', {
                'name': name,
                'description': description,
            })
        
        try:
            project = Project.objects.create(name=name, description=description)
            logging.info(f'创建项目: {project.id}')
            messages.success(request, '项目创建成功')
            return redirect('apitest:project_list')
        except Exception as e:
            messages.error(request, f'创建项目失败: {str(e)}')
            return render(request, 'apitest/project_form.html', {
                'name': name,
                'description': description,
            })
    
    return render(request, 'apitest/project_form.html')

def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    project_id = pk
    
    if request.method == 'POST':
        project.name = request.POST.get('name')
        project.description = request.POST.get('description')

        if Project.objects.filter(name=project.name).exclude(id=project_id).exists():
            messages.error(request, f'项目名称 "{project.name}" 已存在，请使用其他名称')
            return render(request, 'apitest/project_form.html', {
                'name': project.name,
                'description': project.description,
            })
        
        try:
            project.save()
            logging.info(f'更新项目: {project.id}')
            messages.success(request, '项目更新成功')
            return redirect('apitest:project_list')
        except Exception as e:
            messages.error(request, f'更新项目失败: {str(e)}')
            return render(request, 'apitest/project_form.html', {
                'name': project.name,
                'description': project.description,
            })
    
    return render(request, 'apitest/project_form.html', {'project': project})

def project_delete(request, pk):
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=pk)
        test_suites = TestSuite.objects.filter(project=project, deleted=0)
        suite_cases = SuiteCase.objects.filter(suite__in=test_suites)
        for sc in suite_cases:
            sc.delete()
        for suite in test_suites:
            suite.deleted = 1
            suite.save()

        #project.delete()
        project.deleted = 1
        project.save()
        logging.info(f'删除项目: {project.id}')
        messages.success(request, '项目删除成功')
        return redirect('apitest:project_list')
