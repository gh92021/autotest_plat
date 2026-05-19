# apitest/views.py
from django.shortcuts import get_object_or_404
from django.conf import settings
from apitest.models import TestExecution
import logging, os, shutil


def clean_execution(pk):
    execution = get_object_or_404(TestExecution, pk=pk)
    if execution:
        dir = f"{settings.TEST_REPORT_DIR}/{pk}"

        if os.path.exists(dir):
            try:
                shutil.rmtree(dir)
                logging.info(f"清除report目录: {dir}")
            except Exception as e:
                logging.error(f"Error deleting {dir}: {e}")

        execution.delete()
        logging.info(f"执行历史记录已删除: {pk}")

