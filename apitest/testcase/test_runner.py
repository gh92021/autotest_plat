# testapp/test_runner.py
import pytest
import json, logging
import os, time
from pathlib import Path
from django.conf import settings
from apitest.utils.get_parametrize import get_parametrize_kv

class TestRunner:
    
    def __init__(self, execution_id, test_data):
        self.execution_id = execution_id
        self.test_data = test_data
        self.report_dir = Path(settings.TEST_REPORT_DIR) / str(execution_id)
        self.execution_results = []
        
    def gen_test_file(self, test_id, testcases):
        self.report_dir.mkdir(parents=True, exist_ok=True)
        test_file_path = self.report_dir / f'test_case_{test_id}.py'
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(self._gen_pytest_code(testcases))
        return test_file_path
    
    def _gen_pytest_code(self, testcases):
        priority_map = {
            'P0': 'critical',
            'P1': 'high',
            'P2': 'medium',
            'P3': 'low',
            '': 'medium',
        }
        res_file_path = self.report_dir / f'execution_results_{self.execution_id}.json'
        
        code = '''
import pytest
import json
import requests
from apitest.utils.run_api import run_api
from apitest.utils.replace_vars import fill_params, fill_parametrize
from apitest.utils.get_parametrize import get_parametrize_kv
import allure

execution_results = []
_context_vars = {}

def set_var(k, v):
    _context_vars[k] = v

def get_var(v, default=None):
    v = _context_vars.get(v, default)
    return v

def get_all_vars():
    return _context_vars.copy()

'''
        for testcase in testcases:
            testcase_name = testcase.get('name', 'TestCase')
            priority = testcase.get('priority', '')
            severity = priority_map[priority]
            testclass_name = f'TestCase_{self.execution_id}'

            parametrize = testcase.get('parametrize', None)
            if parametrize:
                p_names = get_parametrize_kv(parametrize)[0]
                code += f'''
parametrize = {parametrize}
@pytest.fixture(scope="class", params=get_parametrize_kv(parametrize)[1])
def class_params(request):
'''
                line = ",".join(p_names) + " = request.param\n"
                code += f'''
    {line}
'''
                for k in p_names:
                    code += f'''
    request.cls.{k} = {k}
'''
                code += '''
    yield request.param

@pytest.mark.usefixtures("class_params")
'''
            code += f'''
# 测试用例: {testcase_name}
@allure.title("{testcase_name}")
@allure.severity("{severity}")
@pytest.mark.flaky(reruns=2)
@pytest.mark.flaky(rerun_delay=1)
class TestCase_{self.execution_id}:
    test_failed = False
    
    @classmethod
    def teardown_class(cls):
        try:
'''
            lines = ''
            if testcase.get('teardown_script'):
                teardown_script = testcase.get('teardown_script')
                lines = '\n'.join(f'            {line}' for line in teardown_script.split('\n'))
                code += f'''
{lines}
            print("Teardown completed.")
            execution_results.append({{'teardown_result': "teardown_success"}})
'''
            else:
                code += f'''
            execution_results.append({{'teardown_result': "no_need_teardown"}})
'''
            code += f'''
        except Exception as e:
            print(f"Teardown failed: {{str(e)}}")
            execution_results.append({{'teardown_result': f'teardown_failed: {{str(e)}}'}})
        finally:
            with open('{res_file_path}', 'w', encoding='utf-8') as f:
                json.dump(execution_results, f, ensure_ascii=False, indent=2)
'''
            steps = testcase.get('steps', [])
            for i, step in enumerate(steps):
                step_name = step.get('name', f'Step{i+1}').replace(' ', '_')
                code += f'''
    @allure.step("{step.get('name', f'Step{i+1}')}")
    def test_step{i+1}(self):
        if {testclass_name}.test_failed:
            pytest.skip("跳过此步骤")

        try:
            # 步骤: {step.get('name', f'Step{i+1}')}
            step_result = {{
                'step_name': '{step.get('name', f'Step{i+1}')}',
                'request': {{
                    'url': '{step.get('url')}',
                    'method': '{step.get('method')}',
                }},
                'pre_result': None,
                'post_result': None,
                'assertions': [],
                'asserted': None,
                'step_pass': True
            }}
'''
                if parametrize:
                    p_dict = {}
                    for k in p_names:
                        p_dict_str = "{" + ", ".join(f"'{k}': self.{k}[0]" for k in p_names) + "}"
                    code += f'''
            p_dict = {p_dict_str}
            '''
                if step.get('pre_script'):
                    pre_script = step.get('pre_script')
                    #lines = '\n'.join(f'            {line}' for line in pre_script.split('\n'))
                    code += f"""
            pre_script = '''{pre_script}'''
        """
                    code += f'''
            # 执行前置脚本
            try:
                exec(pre_script, globals())
                step_result['pre_result'] = '前置脚本执行成功'
            except Exception as e:
                step_result['pre_result'] = f'前置脚本执行失败: {{str(e)}}'
                step_result['step_pass'] = False
                execution_results.append(step_result)
                {testclass_name}.test_failed = True
                pytest.fail(f"前置脚本执行失败: {{str(e)}}")
'''
                t = step.get('body', {})
                code += f'''
            # 接口请求
            api_data = {{
                'url': '{step.get('url')}',
                'method': '{step.get('method')}',
                'headers': '{step.get('headers', {})}',
                'params': '{step.get('params', {})}',
                'body': '{step.get('body', {})}'
            }}
            try:
'''
                if parametrize:
                       code += f'''
                api_data['headers'] = fill_parametrize(api_data['headers'], p_dict)
                api_data['params'] = fill_parametrize(api_data['params'], p_dict)
                api_data['body'] = fill_parametrize(api_data['body'], p_dict)
'''
                code += f'''
                api_data['headers'] = fill_params(api_data['headers'], _context_vars)
                api_data['params'] = fill_params(api_data['params'], _context_vars)
                api_data['body'] = fill_params(api_data['body'], _context_vars)
                step_result['request']['body'] = api_data['body']
                step_result['request']['params'] = api_data['params']
                step_result['request']['headers'] = api_data['headers']
                
                response = run_api(api_data)
                step_result['response'] = {{
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'content': response.text,
                    'json': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
                }}
            except Exception as e:
                step_result['response'] = f'接口请求失败: {{str(e)}}'
                step_result['step_pass'] = False
                execution_results.append(step_result)
                {testclass_name}.test_failed = True
                pytest.fail(f"接口请求失败: {{str(e)}}")
'''
                if step.get('post_script'):
                    post_script = step.get('post_script')
                    code += f"""
            post_script = '''{post_script}'''
        """
                    code += f'''
            # 执行后置脚本
            try:
                exec(post_script, globals(), {{'response': response}})
                step_result['post_result'] = '后置脚本执行成功'
            except Exception as e:
                step_result['post_result'] = f'后置脚本执行失败: {{str(e)}}'
                step_result['step_pass'] = False
                execution_results.append(step_result)
                {testclass_name}.test_failed = True
                pytest.fail(f"后置脚本执行失败: {{str(e)}}")
'''
                if step.get('assertions'):
                    lines = step.get('assertions').strip().split('\n')
                    code += '''
            # 执行断言
            all_passed = True
'''
                    for line in lines:
                        line = line.strip()
                        if line:
                            code += f'''
            try:
                {line}
'''                         
                            line = line.replace("'", "\\'")
                            code += f'''
                step_result['assertions'].append({{
                    'assertion': '{line}',
                    'passed': True
                }})
            except Exception as e:
                all_passed = False
                step_result['step_pass'] = False
                step_result['assertions'].append({{
                    'assertion': '{line}',
                    'passed': False,
                    'error': str(e)
                }})
'''
                    code += f'''
            step_result['asserted'] = all_passed
            if not all_passed:
                execution_results.append(step_result)
                {testclass_name}.test_failed = True
                pytest.fail("断言失败")
'''
                else:
                    code += '''
            # 默认断言: 检查状态码
            try:
                assert response.status_code >= 200 and response.status_code < 300, f"接口状态码 {response.status_code}"
                step_result['assertions'].append({
                    'assertion': f"响应状态码 {response.status_code}",
                    'passed': True
                })
                step_result['asserted'] = True
            except Exception as e:
                step_result['assertions'].append({
                    'assertion': "响应状态码",
                    'passed': False,
                    'error': f"接口状态码 {response.status_code}"
                })
                step_result['asserted'] = False
                step_result['step_pass'] = False
                execution_results.append(step_result)
'''
                    code += f'''
                {testclass_name}.test_failed = True
                pytest.fail(f"断言失败: {{str(e)}}")
'''
                code += '''
            execution_results.append(step_result)
'''
                code += f'''
        except Exception:
            pass
'''
        logging.info(f"测试代码生成完成")
        return code
    
    def run(self):
        try:
            test_file = self.gen_test_file(self.execution_id,self.test_data.get('testcases', []))
            logging.info(f"生成测试文件成功：{test_file}")
            
            # report_file = self.report_dir / 'report.html'
            junit_file = self.report_dir / 'report.xml'
            args = [
                str(test_file),
                # f'--html={report_file}',
                # '--self-contained-html',
                f'--alluredir={self.report_dir}/allure-results',
                f'--junitxml={junit_file}',
                '-v',
                '--tb=short',
                '--maxfail=3'
            ]

            logging.info(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}, 开始执行pytest")
            exit_code = pytest.main(args)
            logging.info(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}, pytest执行完成")
            status = 'passed' if exit_code == 0 else 'failed'
            
            total, passed, failed, skipped = self._parse_junit_report(junit_file)
            logging.info(f"解析junit报告完成")            
            result_file = self.report_dir / f'execution_results_{self.execution_id}.json'
            
            if result_file.exists():
                with open(result_file, 'r', encoding='utf-8') as f:
                    self.execution_results = json.load(f)
                logging.info(f"加载执行结果成功：{result_file}")
            
            return {
                'status': status,
                'report_file': str(junit_file),
                'total_tests': total,
                'passed_tests': passed,
                'failed_tests': failed,
                'exit_code': exit_code,
                'execution_results': self.execution_results
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error_message': str(e),
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'execution_results': self.execution_results
            }

    def run_suite(self):
        try:
            testcases = self.test_data.get('testcases', [])
            for testcase in testcases:
                test_file = self.gen_test_file(f'{self.execution_id}_{testcase["test_id"]}', [testcase])
                logging.info(f"生成测试文件成功：{test_file}")
            
            report_file = self.report_dir / 'report.html'
            junit_file = self.report_dir / 'report.xml'

            try:
                import pytest_xdist
                use_xdist = True
            except ImportError:
                use_xdist = False
                logging.info(f"未安装pytest-xdist,单进程执行")
            
            args = [
                str(self.report_dir) + '/',
                # f'--html={report_file}',
                # '--self-contained-html',
                f'--alluredir={self.report_dir}/allure-results',
                f'--junitxml={junit_file}',
                '-v',
                '--tb=short',
            ]
            if use_xdist:
                args.extend([
                    '-n', 'auto',
                    '--dist=loadfile' 
                ])
                logging.info(f"使用pytest-xdist")
            
            logging.info(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}, 开始执行pytest")
            exit_code = pytest.main(args)
            logging.info(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}, pytest执行完成")
            status = 'passed' if exit_code == 0 else 'failed'

            total, passed, failed, skipped = self._parse_junit_report_class(junit_file)
            logging.info(f"解析junit报告完成")
            # if self.report_dir / 'allure-results':
            #     self.gen_allure_report(self.report_dir)
            #     logging.info(f"生成allure报告完成")

            return {
                'status': status,
                'report_file': str(junit_file),
                'total_tests': total,
                'passed_tests': passed,
                'failed_tests': failed,
                'exit_code': exit_code,
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error_message': str(e),
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
            }
        
    def _parse_junit_report(self, junit_file):
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(junit_file)
            root = tree.getroot()
            
            testsuite = root.find('testsuite')
            if testsuite:
                total = int(testsuite.get('tests', 0))
                failures = int(testsuite.get('failures', 0))
                errors = int(testsuite.get('errors', 0))
                skipped = int(testsuite.get('skipped', 0))
                passed = total - failures - errors - skipped
                return total, passed, failures + errors, skipped
            else:
                total = int(root.get('tests', 0))
                failures = int(root.get('failures', 0))
                errors = int(root.get('errors', 0))
                skipped = int(root.get('skipped', 0))
                passed = total - failures - errors - skipped
                return total, passed, failures + errors, skipped
        except:
            return 0, 0, 0, 0
        

    def _parse_junit_report_class(self, junit_file):
        import xml.etree.ElementTree as ET
        tree = ET.parse(junit_file)
        root = tree.getroot()
        class_data = {}
        
        for testcase in root.findall('.//testcase'):
            class_name = testcase.get('classname')
            if class_name not in class_data:
                class_data[class_name] = {'error': 0, 'failed': 0, 'skipped': 0}
            
            if testcase.find('failure') is not None:
                class_data[class_name]['failed'] += 1
            if testcase.find('error') is not None:
                class_data[class_name]['error'] += 1
            if testcase.find('skipped') is not None:
                class_data[class_name]['skipped'] += 1
    
        total = len(class_data)
        failures = errors = skipped = 0
        for class_name in class_data:
            if class_data[class_name]['failed'] > 0 or class_data[class_name]['error'] > 0:
                failures += 1
            elif class_data[class_name]['skipped'] > 0:
                skipped += 1
        passed = total - failures - errors - skipped
        return total, passed, failures + errors, skipped
        
    def gen_allure_report(self, allure_dir):
        import subprocess
        try:
            subprocess.run(
                ["allure", "generate", f"{allure_dir}/allure-results", "-o", f"{allure_dir}/allure-report", "--clean"],
                check=True
            )
        except Exception as e:
            print(f"生成报告失败: {e}")
