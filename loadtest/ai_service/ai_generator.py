# perfapp/ai_generator.py
import json
import requests
import logging
from django.conf import settings
from loadtest.utils.ai_call import call_api
from loadtest.utils.extract_data import extract_code, extract_json
from loadtest.utils.parse_curl import parse_curl_data

class AIGenerator:
    
    def __init__(self):
        self.api_key = settings.DS_API_KEY
        self.api_url = settings.DS_API_URL
    
    def gen_locust_script(self, scenario_desc, api_curls):
        
        prompt = f"""
你是一个资深的性能测试工程师，请根据以下性能测试需求，生成完整的Locust性能测试脚本。

# 测试场景描述：
{scenario_desc}

# 被测接口请求CURL：
{api_curls}

# 要求：
1. 使用Locust的HttpUser类和@task装饰器
2. 包含不同的用户行为场景（使用不同的权重）
3. 设置合理的等待时间（wait_time，使用between方法）
4. 包含请求成功/失败的断言,检查状态码和关键字段
5. 添加on_start方法初始化
6. 生成随机测试数据（用户名、手机号等）
7. 包含异常处理
8. 包含每个task的注释说明和关键的日志记录 
9. 使用with self.client.post(...)等上下文管理器

请生成完整的Python脚本。只输出代码，不要包含额外解释。代码格式要规范。
        """
        
        try:
            #print(prompt)
            response = call_api(prompt, self.api_key, self.api_url)
            #print(response)
            script = extract_code(response)
            return script
        except Exception as e:
            logging.error(f"生成Locust脚本失败: {e}")
            text = 'AI生成Locust脚本失败，生成默认脚本：\n'
            text += self._gen_default_script(api_curls)
            return text
    
    def _gen_default_script(self, api_curls):
        text = f'''
from locust import HttpUser, task, between
import json

class PerformanceTestUser(HttpUser):
    wait_time = between(1, 2)
    
    def on_start(self):
        print("用户启动时执行")
    
    @task(1)
    def test_request(self):
        self.client.get("/")

    def on_stop(self):
        print("done")
'''
        
        api_curls = api_curls.strip()
        if api_curls.startswith('[') and api_curls.endswith(']'):
            curl_list = eval(api_curls)
            curl_data = []
            for curl in curl_list:
                data = parse_curl_data(curl)
                if not data:
                    continue
                curl_data.append(data)
            if len(curl_data) == 0:
                return text

            code = '''
from locust import HttpUser, task, between
import json

class PerformanceTestUser(HttpUser):
    wait_time = between(1, 2)
    
    def on_start(self):
        print("用户启动时执行")
    
'''
            for i, data in enumerate(curl_data):
                code += f'''
    @task(1)
    def test_request_{i}(self):
        headers={data["headers"]}
        params={data["params"]}
        body={data["body"]}

        self.client.{data["method"]}('{data["url"]}', headers=headers, params=params, json=body)
'''
            return code
        else:
            return text
        
    
    def gen_test_data(self, api_curls, cnt=100):

        prompt = f"""
请生成{cnt}条测试数据，用于性能测试。

# 被测接口请求CURL： 
{api_curls}

# 要求：
1. 数据要真实合理，符合实际业务场景
2. 覆盖边界值和异常情况（如用户名长度边界、密码复杂度等）
3. 不要包含任何额外解释，直接输出JSON

请以JSON格式返回数据。示例:
{{"test_data": [
    {{"field1": "value1", "field2": "value2"}},
    ...
]}}
        """
        
        try:
            #print(prompt)
            response = call_api(prompt, self.api_key, self.api_url)
            #print(response)
            data = extract_json(response)
            return data
        except Exception as e:
            logging.error(f"生成测试数据失败: {e}")
            return '{}'
    
