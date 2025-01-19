# Monnet Gateway

# Notes
    pytest need __init__.py on main package and modules

# Payload

Recive
{
    "command": playbook
    "data": {
        "playbook": "mi_playbook.yml",
        "extra_vars": {
            "var1": "valor1",
            "var2": "valor2"
        },
        "ip": "192.168.1.100",
        "limit": "mi_grupo"
        "user": "user" # optional
    }
}

# Netcat test

```
echo '{"command": "playbook", "data": {"playbook": "test.yml"}}' | nc localhost 65432
echo '{"command": "playbook", "data": {"playbook": "test.yml", "extra_vars": {"var1": "value1", "var2": "value2"}}}' | nc localhost 65432
echo '{"command": "playbook", "data": {"playbook": "linux-df.yml", "extra_vars": {}, "ip": "192.168.2.148"}}' | nc localhost 65432
echo '{"command": "playbook", "data": {"playbook": "linux-df.yml", "extra_vars": {}, "ip": "192.168.2.148", "user": "ansible"}}' | nc localhost 65432
```

## Planing structure

```
monnet_gateway/
│   ├── __init__.py         # Indica que este es un paquete Python
│   ├── main.py             # Punto de entrada principal (equivalente al actual `monnet_gateway.py`)
│   ├── server.py           # Lógica del servidor (sockets, conexiones, hilos)
│   ├── handlers/
│   │   ├── __init__.py     # Inicialización del paquete de handlers
│   │   ├── ansible_handler.py # Comandos relacionados con Ansible
│   │   ├── task_handler.py # Comandos relacionados con tareas independientes
│   │   └── ...             # Otros handlers
│   ├── utils/
│   │   ├── __init__.py     # Inicialización del paquete de utilidades
│   │   ├── logger.py       # Funciones de logging
│   │   ├── config.py       # Configuración global (variables HOST, PORT, etc.)
│   │   └── helpers.py      # Funciones auxiliares (e.g., manejo de JSON, validaciones)
│   └── tasks/
│       ├── __init__.py     # Inicialización del paquete de tareas
│       ├── task_manager.py # Gestión de tareas independientes
│       └── ...             # Otras tareas
├── playbooks/              # Carpeta de playbooks Ansible
└── README.md               # Documentación del proyecto
```