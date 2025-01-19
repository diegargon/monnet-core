# Monnet Agent

Agent Client to install on other hosts and send stats and otheers can be installed manually or via ui/ansible

Support: Linux

Planning Support: Windows, and probably others non-POSIX

## Install Monnet Agent Linux (systemd)

Via UI and ansible is the easy/fast way

For manually processs check the ansible playbook install-agent-systemd

## Payload Structure Documentation

```
{
    'id': str,                # Unique Host identifier
    'cmd': str,               # Command to execute. Example: "ping"
    'token': str,             # Authentication token. Example: "73a7a18ce78742aa8aadacbe6a918dd8"
    'interval': int,          # Interval in seconds
    'version': str,           # Version software. Example:
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
## Response Structure Documentation

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

