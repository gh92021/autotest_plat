# apitest/utils/tasks.py
from auto_test.celery import shared_task
from celery.schedules import crontab
from apitest.models import TestExecution, TestCase
from apitest.utils.clean_history import clean_execution
from apitest.utils.inspect import run_inspect
from datetime import datetime, timedelta

@shared_task
def clean_old_executions():
    executions = TestExecution.objects.filter(created_at__lt=datetime.now() - timedelta(days=15))
    for exe in executions:
        clean_execution(exe.id)    
    return "Cleanup completed"

@shared_task
def inspect_daily():
    test_cases = TestCase.objects.filter(deleted=0, is_active=True)
    for tc in test_cases:
        run_inspect(tc)    
    return "Inspect process completed"
