# apitest/views.py
from django.shortcuts import get_object_or_404
from django.conf import settings
from apitest.models import TestCase
from apitest.utils.run_api import run_api, get_request_data
from apitest.utils.replace_vars import fill_parametrize
import logging, os, json
from apitest.models import Globals

def run_inspect(pk):
    test_case = get_object_or_404(TestCase, pk=pk)
    res = run_case_test(test_case)

    if not res:
        test_case.inspect_failures += 1
        logging.info(f"测试用例 {test_case.id} 巡检失败")
        if test_case.inspect_failures >= 5:
            test_case.is_active = False
            logging.info(f"测试用例 {test_case.id} 巡检连续失败5次，已禁用")
            test_case.inspect_failures = 0
    else:
        test_case.inspect_failures = 0

    test_case.save()
    return True

def run_case_test(testcase):
    try:
        globals = Globals.objects.all()
        locals = testcase.vars.filter(is_parametrize=False).first()
        if locals:
            locals = locals.var_value
        locals = json.loads(locals) if locals else {}
        
        parametrize = testcase.vars.filter(is_parametrize=True).first()
        if parametrize:
            parametrize = parametrize.var_value
        parametrize = json.loads(parametrize)[0] if parametrize else {}
        
        _context_vars = {}
        steps = testcase.steps.all()
        
        for step in steps:
            api = step.api
            if not api:
                return False
            env = api.env
            if not env:
                return False

            if step.pre_script:
                try:
                    exec(step.pre_script, globals(), _context_vars)
                except Exception as e:
                    return False

            locals.update(_context_vars)
            tc_data = get_request_data(api, env, step, locals, globals)
            tc_data['headers'] = fill_parametrize(tc_data['headers'], parametrize)
            tc_data['params'] = fill_parametrize(tc_data['params'], parametrize)
            tc_data['body'] = fill_parametrize(tc_data['body'], parametrize)
            try:
                response = run_api(tc_data)
            except Exception as e:
                return False

            if step.post_script:
                try:
                    exec(step.post_script, globals(), {'response': response})
                except Exception as e:
                    return False

            assertions = []                
            try:
                if step.assertions:
                    assertion_lines = step.assertions.strip().split('\n')
                    for line in assertion_lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            exec(line, globals(), {'response': response})
                        except Exception as e:
                            return False
                else:
                    try:
                        assert response.status_code >= 200 and response.status_code < 300, f"接口状态码 {response.status_code}"
                    except Exception as e:
                        return False

            except Exception as e:
                return False
            
        teardown_script = testcase.teardown_script
        if teardown_script:
            try:
                exec(teardown_script, globals())
            except Exception as e:
                logging.info(f"Teardown failed: {str(e)}")
            
        return True
        
    except Exception as e:
        return False