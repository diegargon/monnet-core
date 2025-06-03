"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent

Misc utils
"""
import json
from collections import defaultdict
import uuid
import os

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
    if isinstance(obj1, list) and isinstance(obj2, list):
        if len(obj1) != len(obj2):
            return False
        return all(deep_compare(i, j) for i, j in zip(obj1, obj2))

    return obj1 == obj2

def generate_machine_id_like() -> str:
    """
    Genera un UID en formato idéntico a /etc/machine-id (32 caracteres hex, minúsculas, sin guiones).
    """
    return uuid.uuid4().hex


def create_machine_id(path="/etc/machine-id") -> str:
    """
    Crea un ID de máquina único en formato idéntico a /etc/machine-id.
    Si el archivo ya existe, no lo sobrescribe y devuelve el contenido existente.
    Si no existe, lo crea con un nuevo ID y lo devuelve.
    Args:
        path (str): Ruta al fichero machine-id (por defecto /etc/machine-id).
    Returns:
        str: machine-id (32 caracteres hex, minúsculas, sin guiones).
    """
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                machine_id = f.read().strip()
                if machine_id:
                    return machine_id
        machine_id = generate_machine_id_like()
        with open(path, "w", encoding="utf-8") as f:
            f.write(machine_id + "\n")
        return machine_id
    except Exception as e:
        raise RuntimeError(f"Error al crear machine-id: {e}")
