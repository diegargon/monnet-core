# Monnet Gateway


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