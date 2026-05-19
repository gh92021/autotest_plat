import pytest
import json

def get_parametrize_kv(data):
    if type(data) == str:
        data = json.loads(data)
    values = []
    keys = []
    for k in data[0].keys():
        keys.append(k)
    keys = tuple(keys)

    for item in data:
        tp = []
        for v in item.values():
            tp.append(v)
        values.append(tuple(tp))
    return keys, values

def handle_param_fixture(keys, values):
    code = ",".join(keys) + " = request.param\n"
    for k in keys:
        code += f"request.cls.{k} = {k}\n"
    print(code)


if __name__ == '__main__':
    js = [{
        "a": "aa1",
        "b": "bb1",
        "u": "u1",
    },{
        "a": "aa2",
        "b": "bb2",
        "u": "u2",
    }]
    js = json.dumps(js)
    print(get_parametrize_kv(js)[0])
    print(get_parametrize_kv(js)[1])
    handle_param_fixture(js)
