# Monnet Gateway

Mediates between web ui and the system

At this momment is optional only used for  ansible features.

Will be mandatory.


## Install

```
mkdir /opt/monnet-core

cd /opt/monnet-core

git clone https://github.com/diegargon/monnet-core.git

cp files/monnet-gateway.service  /etc/systemd/system

systemctl enable  monnet-gateway.service

systemctl start  monnet-gateway.service
```

## Notes

pytest need __init__.py on main package and modules

## Payload

Receive

```
{
    "command": playbook
    "data": {
        "playbook": "mi_playbook.yml",
        "extra_vars": {
            "var1": "valor1",
            "var2": "valor2"
        },
        "ip": "192.168.1.100",
        "limit": "mi_grupo" #optional
        "user": "user" # optional
    }
}
```

## Netcat test examples

```
echo '{"command": "playbook", "data": {"playbook": "test.yml"}}' | nc localhost 65432
echo '{"command": "playbook", "data": {"playbook": "test.yml", "extra_vars": {"var1": "value1", "var2": "value2"}}}' | nc localhost 65432
echo '{"command": "playbook", "data": {"playbook": "ansible-ping.yml", "extra_vars": {}, "ip": "192.168.2.148"}}' | nc localhost 65432
echo '{"command": "playbook", "data": {"playbook": "ansible-ping.yml", "extra_vars": {}, "ip": "192.168.2.148", "user": "ansible"}}' | nc localhost 65432
```

## Planing structure (deprecated)

```
    files/                          # Other files systemd
    shared/                         # Shared modules
    constants/                      # Shared Constants
    monnet_gateway/
    │   ├── mgateway.py                 # Punto de entrada principal (equivalente al actual `monnet_gateway.py`)
    │   ├── server.py               # Lógica del servidor (sockets, conexiones, hilos)
    │   ├── handlers/
    │   │   ├── handler_ansible.py  # Comandos relacionados con Ansible
    │   │   ├── handler_client.py   # Comandos relacionados con tareas independientes
    │   │   └── ...                 # Otros handlers
    │   ├── utils/
    │   │   ├── logger.py           # Funciones de logging
    │   │   ├── config.py           # Configuración global (variables HOST, PORT, etc.)
    │   │   └── helpers.py          # Funciones auxiliares (e.g., manejo de JSON, validaciones)
    │   └── tasks/
    │       ├── task_manager.py     # Gestión de tareas independientes
    │       └── ...                 # Otras tareas
    ├── playbooks/                  # Carpeta de playbooks Ansible
    └── README.md                   # Documentación del proyecto

```