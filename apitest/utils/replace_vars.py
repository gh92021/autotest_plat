import re
import json

def fill_params(text, d):
    if not text:
        return text
    pattern = r'\{\{(\w+)\}\}'
    
    def replace_match(match):
        var_name = match.group(1)
        return d.get(var_name, match.group(0))
    
    return re.sub(pattern, replace_match, text)

def fill_parametrize(text, d):
    if not text:
        return text
    pattern = r'\$\{(\w+)\}'
    
    def replace_match(match):
        var_name = match.group(1)
        return d.get(var_name, match.group(0))
    
    return re.sub(pattern, replace_match, text)



if __name__ == "__main__":
    strs = '{"a":1,"b":"2"}'
    r = fill_parametrize(strs)
    print(r)
    '''original_str = '{"a":"123{{aa}}456","b":"{{aa}}_{{bb}}","c":{{cc}}}'
    params_dict = {"cc": "111", "bb": "bb"}
    result = fill_params(original_str, params_dict)
    
    print("原字符串:", original_str)
    print("替换结果:", result)'''