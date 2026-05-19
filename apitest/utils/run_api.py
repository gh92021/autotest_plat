import requests
import json
from .replace_vars import fill_params

def run_api(api_data):
    url = api_data['url']
    method = api_data['method'].upper()
    headers = api_data.get('headers', {})
    params = api_data.get('params', {})
    body = api_data.get('body', None)

    params = json.loads(params) if params else {}
    body = json.loads(body) if body else None
    headers = json.loads(headers) if headers else {}
    json_body, data = None, None

    if headers.get('content-type', '').startswith('application/json') or not headers.get('content-type', ''):
        json_body = body
    else:
        data = body
    if not url.startswith('http'):
        url = 'http://' + url
    
    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        data=data,
        json=json_body
    )
    
    return response

def get_request_data(api, env, step, locals={}, globals={}):
    url = env.base_url.rstrip('/') + '/' + api.url.lstrip('/')
    headers = api.headers
    params = api.params
    body = api.body

    var_dict = {}    
    if locals:
        var_dict = locals
    if globals:
        globals = {p[0]: p[1] for p in globals.values_list('name', 'value')}
        var_dict.update(globals)
    
    if step.replace_params:
        params = step.replace_params
    if step.replace_body:
        body = step.replace_body

    headers = fill_params(headers, var_dict)
    params = fill_params(params, var_dict)
    body = fill_params(body, var_dict)

    tc_data = {
            'url': url,
            'method': api.method,
            'headers': headers,
            'params': params,
            'body': body,
        }
    return tc_data