import requests
import logging
import time

def call_api(prompt, api_key, api_url):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'deepseek-v4-pro',
        'messages': [
            {'role': 'system', 'content': '你是一个专业的性能测试工程师，擅长理解拆分性能场景需求、编写Locust性能测试脚本和分析性能数据。'},
            {'role': 'user', 'content': prompt}
        ],
        "thinking": {"type": "disabled"},
        "stream": False,
        'temperature': 0.7,
        'max_tokens': 4096
    }
    
    for i in range(3):
        try:
            response = requests.post(api_url, headers=headers, json=data, timeout=60)
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    logging.info("DeepSeek API调用成功")
                    return result['choices'][0]['message']['content']
                else:
                    raise Exception("API返回格式错误")
            else:
                logging.error(f"DeepSeek API调用失败: {response.status_code}")
                raise Exception(f"DeepSeek API调用失败: {response.status_code}")
        except Exception as e:
            logging.info(f"重试 {i + 1}/3")
            time.sleep(0.5)
            if i == 2:
                logging.error(f"DeepSeek API错误: {e}")
                raise e
