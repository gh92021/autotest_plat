import json
import requests
import logging
from loadtest.utils.ai_call import call_api
from loadtest.utils.extract_data import extract_json
from django.conf import settings

class ResultAnalyzer:
    def __init__(self):
        self.api_key = settings.DS_API_KEY
        self.api_url = settings.DS_API_URL
    
    def analyze_report(self, task, stats):

        prompt = f"""你是一个资深的性能测试工程师，请分析以下性能测试数据，输出分析报告和优化建议：

# 测试配置：
- 并发用户数：{task.users}
- 启动速率：{task.spawn_rate} 用户/秒
- 运行时长：{task.run_time}秒
        
# 测试统计数据：
{stats}

请思考以下问题：
1. 系统性能是否达标？请给出评价和改进建议。
2. 是否存在明显的性能瓶颈？
3. 针对响应时间异常，可能的原因是什么？
4. 请提供具体的优化方案（包括代码、数据库、架构等方面）。

# 要求：
1. summary要客观评估系统性能表现
2. 根据P95和平均响应时间判断性能等级
3. 根据失败率判断系统稳定性
4. 建议要具体、可操作
5. 直接输出JSON，不要有其他文字

JSON格式输出示例：
{{
    "summary": "整体性能评估结果",
    "issues": "问题或性能瓶颈分析",
    "suggestions": [
        "优化建议1",
        "优化建议2",
        ...
    ]
}}"""
        
        #print(prompt)
        try:
            response = call_api(prompt, self.api_key, self.api_url)
            return extract_json(response)
        except Exception as e:
            logging.error(f"{e}")
            return {
                'summary': '调用AI失败，未进行深入分析',
                'suggestions': ['调用AI失败，未进行深入分析'],
                'issues': '调用AI失败，未进行深入分析'
            }

    