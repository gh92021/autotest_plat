from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class TestScript(models.Model):
    """测试脚本"""
    name = models.CharField(max_length=200, verbose_name='脚本名称')
    scenario = models.TextField(blank=True, verbose_name='场景描述')
    target_url = models.CharField(max_length=200, default='', verbose_name='目标URL')
    api_curls = models.TextField(blank=True, verbose_name='接口CURL')
    script_content = models.TextField(blank=True, verbose_name='Locust脚本内容')
    testdata = models.TextField(blank=True, help_text='测试数据配置JSON')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '测试脚本'
        verbose_name_plural = '测试脚本'
        ordering = ['-created_at']

class TestTask(models.Model):
    """测试任务"""
    MODE_CHOICES = [
        ('standalone', '单机模式'),
        ('distributed', '分布式模式'),
    ]
    STATUS_CHOICES = [
        ('pending', '未开始'),
        ('running', '执行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('stopped', '已停止'),
    ]
    name = models.CharField(max_length=200, verbose_name='任务名称')
    script = models.ForeignKey(TestScript, on_delete=models.CASCADE, related_name='tasks', verbose_name='测试脚本')

    users = models.IntegerField(default=10, verbose_name='并发用户数')
    spawn_rate = models.IntegerField(default=1, verbose_name='启动速率(用户/秒)')
    run_time = models.CharField(max_length=60, default='运行时间(秒)', verbose_name='运行时间')

    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='standalone')
    worker_nodes = models.JSONField(default=list, help_text='工作节点列表', verbose_name='工作节点')
    master_host = models.CharField(max_length=200, blank=True, verbose_name='主节点地址')
    master_port = models.IntegerField(default=5557, verbose_name='主节点端口')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    process_id = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '测试任务'
        verbose_name_plural = '测试任务'
        ordering = ['-created_at']

class TestResult(models.Model):
    """测试结果"""
    task = models.ForeignKey(TestTask, on_delete=models.CASCADE, related_name='results')
    timestamp = models.DateTimeField(auto_now_add=True)
    task_stamp = models.IntegerField(default=0)
    # 实时统计数据
    current_users = models.IntegerField(default=0)
    total_requests = models.IntegerField(default=0)
    current_rps = models.FloatField(default=0)
    avg_response_time = models.FloatField(default=0)
    cur_fail_ratio = models.FloatField(default=0)
    raw_data = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-timestamp']

class TaskRecord(models.Model):
    """执行记录"""
    task = models.ForeignKey(TestTask, on_delete=models.CASCADE, related_name='records')
    task_stamp = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    total_requests = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0)
    rps = models.FloatField(default=0.0, verbose_name='每秒请求数')
    fail_ratio = models.FloatField(default=0, verbose_name='失败率')
    
    class Meta:
        ordering = ['-created_at']

class TestReport(models.Model):
    """测试报告"""
    task = models.ForeignKey(TestTask, on_delete=models.CASCADE, related_name='report')
    record = models.ForeignKey(TaskRecord, null=True, blank=True, on_delete=models.CASCADE, related_name='report')
    report_file = models.CharField(max_length=500, verbose_name='报告文件路径')
    summary = models.TextField(blank=True, verbose_name='测试总结')
    issues = models.TextField(blank=True, verbose_name='问题描述')
    suggestions = models.TextField(blank=True, verbose_name='优化建议')
    created_at = models.DateTimeField(auto_now_add=True)

class WorkerNode(models.Model):
    """工作节点"""
    STATUS_CHOICES = [
        ('online', '在线'),
        ('offline', '离线'),
        ('busy', '忙碌'),
    ]
    name = models.CharField(max_length=100, unique=True)
    host = models.CharField(max_length=200)
    port = models.IntegerField(default=5557)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    current_test = models.ForeignKey(TestTask, null=True, blank=True, on_delete=models.SET_NULL)
    last_active = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name