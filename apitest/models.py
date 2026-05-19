from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Project(models.Model):
    """项目"""
    name = models.CharField(max_length=100, unique=True, verbose_name='项目名称')
    description = models.TextField(blank=True, verbose_name='项目描述')
    created_at = models.DateTimeField(auto_now_add=True)
    deleted = models.SmallIntegerField(default=0, verbose_name='是否删除')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '项目'
        verbose_name_plural = '项目'
        ordering = ['-created_at']
        
class Module(models.Model):
    """服务"""
    name = models.CharField(max_length=100, unique=True, verbose_name='服务名称')
    description = models.TextField(blank=True, verbose_name='服务描述')
    git_url = models.TextField(blank=True, verbose_name='Git仓库URL')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '服务'
        verbose_name_plural = '服务'
        ordering = ['-created_at']

class Env(models.Model):
    """环境"""
    name = models.CharField(max_length=100, unique=True, verbose_name='环境名称')
    description = models.TextField(blank=True, verbose_name='环境描述')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='env', verbose_name='所属服务')
    base_url = models.CharField(max_length=150, verbose_name='环境基础URL')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '环境'
        verbose_name_plural = '环境'
        ordering = ['-created_at']

class Globals(models.Model):
    """全局变量"""
    name = models.CharField(max_length=100, unique=True, verbose_name='全局变量名称')
    value = models.TextField(blank=True, verbose_name='全局变量值')
    description = models.TextField(blank=True, verbose_name='全局变量描述')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '全局变量'
        verbose_name_plural = '全局变量'
        ordering = ['name']

class Api(models.Model):
    """接口"""
    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='接口名称')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='apis', verbose_name='所属服务')
    env = models.ForeignKey(Env, on_delete=models.SET_NULL, null=True, related_name='apis', verbose_name='环境')
    url = models.CharField(max_length=500, verbose_name='请求路径')
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default='GET', verbose_name='请求方法')
    headers = models.TextField(default='{}', help_text='JSON格式', verbose_name='请求头')
    params = models.TextField(default='{}', help_text='JSON格式', verbose_name='查询参数')
    body = models.TextField(default='{}', help_text='JSON格式', verbose_name='请求体')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '接口'
        verbose_name_plural = '接口'
        ordering = ['-updated_at']

class TestCase(models.Model):
    """测试用例"""
    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
    ]
    PRIORITY_CHOICES = [
        ('P0', 'P0'),
        ('P1', 'P1'),
        ('P2', 'P2'),
        ('P3', 'P3'),
    ]
    name = models.CharField(max_length=200, verbose_name='用例名称')
    priority = models.CharField(max_length=5, choices=PRIORITY_CHOICES, default='', verbose_name='优先级')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='testcases', verbose_name='所属项目')
    teardown_script = models.TextField(blank=True, help_text='teardown', verbose_name='teardown脚本')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    inspect_failures = models.IntegerField(default=0, verbose_name='巡检失败次数')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.SmallIntegerField(default=0, verbose_name='是否删除')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '测试用例'
        verbose_name_plural = '测试用例'
        ordering = ['-updated_at']

class Steps(models.Model):
    """测试用例关联步骤"""
    
    name = models.CharField(max_length=200, verbose_name='步骤名称')
    testcase = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='steps', verbose_name='测试用例')
    api = models.ForeignKey(Api, on_delete=models.SET_NULL, null=True, related_name='steps', verbose_name='接口')
    replace_params = models.TextField(blank=True, help_text='JSON格式', verbose_name='替换查询参数')
    replace_body = models.TextField(blank=True, help_text='JSON格式', verbose_name='替换请求体')
    pre_script = models.TextField(blank=True, help_text='pass', verbose_name='前置脚本')
    post_script = models.TextField(blank=True, help_text='pass', verbose_name='后置脚本')
    assertions = models.TextField(blank=True, help_text='pass', verbose_name='断言')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '测试步骤'
        verbose_name_plural = '测试步骤'

class Parameters(models.Model):
    """测试用例关联参数"""
    
    var_name = models.CharField(max_length=200, verbose_name='变量名')
    var_value = models.CharField(max_length=500, verbose_name='变量值')
    testcase = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='vars', verbose_name='测试用例')
    is_parametrize = models.BooleanField(default=False, verbose_name='参数化变量')
    
    def __str__(self):
        return self.var_name
    
    class Meta:
        verbose_name = '测试用例参数'
        verbose_name_plural = '测试用例参数'

class TestSuite(models.Model):
    """测试计划"""
    name = models.CharField(max_length=100, verbose_name='套件名称')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='suites', verbose_name='所属项目')
    testcases = models.ManyToManyField(TestCase, through='SuiteCase', verbose_name='测试用例')
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.SmallIntegerField(default=0, verbose_name='是否删除')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '测试套件'
        verbose_name_plural = '测试套件'
        ordering = ['-created_at']

class SuiteCase(models.Model):
    """计划关联用例"""
    suite = models.ForeignKey(TestSuite, on_delete=models.CASCADE)
    testcase = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    order = models.IntegerField(default=0, verbose_name='执行顺序')
    
    class Meta:
        ordering = ['order']
        unique_together = ['suite', 'testcase']

class TestExecution(models.Model):
    """测试执行记录"""
    STATUS_CHOICES = [
        ('pending', '等待执行'),
        ('running', '执行中'),
        ('passed', '通过'),
        ('failed', '失败'),
        ('error', '错误'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='执行名称')
    execution_type = models.CharField(max_length=20, choices=[('case', '测试用例'), ('suite', '测试计划')])
    target_id = models.IntegerField(verbose_name='用例或计划ID')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    report_file = models.CharField(max_length=500, blank=True, verbose_name='报告文件')
    total_tests = models.IntegerField(default=0)
    passed_tests = models.IntegerField(default=0)
    failed_tests = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.created_at}"
    
    class Meta:
        verbose_name = '测试执行记录'
        verbose_name_plural = '测试执行记录'
        ordering = ['-created_at']