"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2024 Diego Garcia (diego/@/envigo.net)

Monnet Agent

Misc utils
"""
import json
from collections import defaultdict

def normalize(data):
    """ NOT USED """
    if isinstance(data, defaultdict):
        return {k: normalize(v) for k, v in data.items()}

    if isinstance(data, dict):
        return {k: normalize(v) for k, v in data.items()}

    if isinstance(data, list):
        return [normalize(v) for v in data]

    if isinstance(data, tuple):  # Convierte tuplas en listas
        return list(data)

    if isinstance(data, (str, int, float, bool)) or data is None:
        return data
    else:
        return str(data)

def are_equal(obj1, obj2):
    """ NOT USED """
    json1 = json.dumps(obj1, sort_keys=True)
    json2 = json.dumps(obj2, sort_keys=True)
    return json1 == json2


def deep_compare(obj1, obj2):
    """ NOT USED """
    if isinstance(obj1, dict) and isinstance(obj2, dict):
        if obj1.keys() != obj2.keys():
            return False
        return all(deep_compare(obj1[k], obj2[k]) for k in obj1)
    elif isinstance(obj1, list) and isinstance(obj2, list):
        if len(obj1) != len(obj2):
            return False
        return all(deep_compare(i, j) for i, j in zip(obj1, obj2))
    else:
        return obj1 == obj2
