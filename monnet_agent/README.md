# Monnet Agent

The agent client is installed on other hosts to send stats and other data to the Monnet server. It can be installed manually or via UI/Ansible.

Support: Linux

Planned Support: Windows, and possibly other non-POSIX systems.

## Install Monnet Agent Linux (systemd)

Using the UI/Ansible is the easiest and fastest way.

Works better with a systemd Linux; no other startup script is provided at this moment. Using the Ansible agent installer will skip installing the startup script if it does not detect a systemd machine.

Python: The automatic process will install some dependencies on the hosts: `psutil`.

For manual installation, check the Ansible playbook `monnet-gateway/playbooks/install-monnet-agent-systemd`.

# Technical Info

## Payload Structure Documentation (probably outdated)

```
{
    'id': str,                # Unique Host identifier
    'cmd': str,               # Command to execute. Example: "ping"
    'token': str,             # Authentication token. Example: "73a7a18ce78742aa8aadacbe6a918dd8"
    'interval': int,          # Interval in seconds
    'version': str,           # Software version. Example:
    'data': {                 # Contains other info
        'mydata': {
            'data1': 1,
            'data2': 1,
            'data3': 1
        }
    },
    'meta': {                 # Metadata about the payload source and environment.
        'timestamp': str,     # ISO 8601 timestamp of when the payload was generated.
        'timezone': str,      # Time zone identifier.
        'hostname': str,      # Hostname of the system that generated the payload.
        'nodename': str,      # Nodename of the system.
        'ip_address': str,    # IP address of the system.
        'agent_version': str, # Version of the agent that generated the payload.
        'uuid': str           # Unique identifier (UUID) of the system or agent.
    }
}
```

## Response Structure Documentation (probably outdated)

```
{
    'cmd': str,              # Command response type. Example: "pong"
    'token': str,            # Token used for authentication or identification.
    'version': float,        # Version of the response or system. Example: 0.22
    'response_msg': bool,    # Indicates if the response message is successful. Example: True
    'refresh': int,          # Refresh interval in seconds. Example: 5
    'data': list             # List of data, typically empty in this case. Example: []
}
```

