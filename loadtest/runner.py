# perfapp/locust_runner.py
import subprocess
import os
import signal
import time
import logging
import json
from django.conf import settings
from datetime import datetime
from loadtest.models import TestResult

class LocustRunner:
    
    def __init__(self, task, stamp):
        self.task = task
        self.task_stamp = stamp
        self.process = None
        self.process_wk = []
        self.script = self.task.script
        self.script_path = settings.LOCUST_SCRIPTS_DIR / f'script_{self.script.id}.py'    
        self.report_dir = settings.REPORTS_DIR / f'test_{self.task.id}_{stamp}'
    
    def run_standalone(self):
        logging.info(f'{self.task.id}: 单机模式')
        script_path = self.script_path
        if not script_path.exists():
            self.task.status = 'failed'
            self.task.save()
            return None
        
        report_dir = self.report_dir
        report_dir.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            'locust',
            '-f', str(script_path),
            '--host', self.script.target_url,
            '--users', str(self.task.users),
            '--spawn-rate', str(self.task.spawn_rate),
            '--run-time', f'{self.task.run_time}s',
            '--headless',
            '--only-summary',
            '--html', str(report_dir / 'report.html'),
            '--csv', str(report_dir / 'stats'),
            '--json',
        ]
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logging.info(f'{self.task.id}: 单机模式进程启动，PID: {self.process.pid}')
        self.task.process_id = self.process.pid
        self.task.status = 'running'
        self.task.save()
        return self.process
    
    def run_master(self):
        # 分布式主节点运行
        logging.info(f'{self.task.id}: 主节点开始')
        script_path = self.script_path
        if not script_path.exists():
            self.task.status = 'failed'
            self.task.save()
            return None
        
        report_dir = self.report_dir
        report_dir.mkdir(parents=True, exist_ok=True)
        worker_nodes = json.loads(self.task.worker_nodes)
        
        # 启动主节点
        cmd = [
            'locust',
            '-f', str(script_path),
            '--host', self.script.target_url,
            '--users', str(self.task.users),
            '--spawn-rate', str(self.task.spawn_rate),
            '--master',
            '--master-bind-host', self.task.master_host or '0.0.0.0',
            '--master-bind-port', str(self.task.master_port),
            '--expect-workers', str(len(worker_nodes)),
            '--run-time', f'{self.task.run_time}s',
            '--headless',
            '--only-summary',
            '--json',
            '--html', str(report_dir / 'report.html'),
            '--csv', str(report_dir / 'stats'),
        ]
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logging.info(f'{self.task.id}: 主节点进程启动，PID: {self.process.pid}')
        self.task.process_id = self.process.pid
        self.task.save()
        return self.process
    
    def run_worker(self, master_host, master_port=5557):
        # 分布式工作节点运行
        logging.info(f'{self.task.id}: 工作节点开始')
        script_path = self.script_path
        if not script_path.exists():
            self.task.status = 'failed'
            self.task.save()
            return None
        
        cmd = [
            'locust',
            '-f', str(script_path),
            '--worker',
            '--master-host', master_host,
            '--master-port', str(master_port),
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logging.info(f'{self.task.id}: 工作节点进程启动，PID: {process.pid}')
        self.process_wk.append(process)
        return process
    
    def stop(self):
        if self.process:
            #os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process.terminate()
            self.process.wait(timeout=10)
            logging.info(f'{self.task.id}: 进程已终止')
        if self.process_wk:
            for process in self.process_wk:
                process.terminate()
                process.wait(timeout=10)
                logging.info(f'{self.task.id}: 工作节点进程已终止')
            
        self.task.status = 'stopped'
        self.task.completed_at = datetime.now()
        self.task.save()
    
    def monitor_stats(self):
        # 监控测试统计,每5秒采集一次
        import csv
        stats_file = self.report_dir / 'stats_stats.csv'
        history_file = self.report_dir / 'stats_stats_history.csv'
        
        while self.task.status == 'running':
            try:
                if self.process and self.process.poll() is not None:
                    self.task.status = 'completed'
                    self.task.completed_at = datetime.now()
                    self.task.save()
                    break
                    
                if stats_file.exists() and history_file.exists():
                    with open(stats_file, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                        result = self._parse_stats(rows)

                    with open(history_file, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                        if rows:
                            user_cnt = int(rows[-1].get('User Count', 0))
                        
                    TestResult.objects.create(
                        task=self.task,
                        task_stamp=self.task_stamp,
                        current_users=user_cnt,
                        total_requests=result['total_requests'],
                        current_rps=round(result['total_rps'], 2),
                        avg_response_time=round(result['avg_response_time'], 2),
                        cur_fail_ratio=round(result['fail_ratio'], 4),
                        raw_data={'rows': rows}
                    )
                    logging.info(f'{self.task.id}: 监控线程采集统计信息')
                
                time.sleep(5)
            except Exception as e:
                logging.error(f'{self.task.id}: 监控采集失败: {str(e)}')
                break
        logging.info(f'{self.task.id}: 监控线程结束')
    
    def _parse_stats(self, rows):
        # 解析测试统计数据
        if rows:
            total_requests = int(rows[-1].get('Request Count', 0))
            total_failures = int(rows[-1].get('Failure Count', 0))
            fail_ratio = total_failures / (total_requests + total_failures) if (total_requests + total_failures) > 0 else 0
            total_rps = float(rows[-1].get('Requests/s', 0))
            avg_response_time = float(rows[-1].get('Average Response Time', 0))

        result = {
            'total_requests': total_requests,
            'total_failures': total_failures,
            'fail_ratio': fail_ratio,
            'avg_response_time': avg_response_time,
            'total_rps': total_rps
        }
        return result