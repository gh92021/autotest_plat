from curl_parsers import parse_curl

def parse_curl_data(curl):
    try:
        raw_data = parse_curl(curl)
        json_data = raw_data.get('json_data', None)
        form_data = raw_data.get('form_data', None)
        data_raw = raw_data.get('raw_data', None)
        body = None
        if json_data:
            body = json_data
        elif form_data:
            body = form_data
        elif data_raw:
            body = data_raw

        data = {
            'url': raw_data.get('url', ''),
            'method': raw_data.get('method', ''),
            'headers': raw_data.get('headers', {}),
            'body': body,
            'params': raw_data.get('params', {}),
        }
        
    except Exception as e:
        return {'data': {}, 'error': str(e)}
    return data