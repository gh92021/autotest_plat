import json
import re

def extract_code(response):
    patterns = [
        r'```python(.*?)```',
        r'```(.*?)```',
        r'`(.*?)`'
    ]
    for pattern in patterns:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
    return response
    
def extract_json(response):
    try:
        return json.loads(response)
    except:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        raise Exception("无法解析JSON")
