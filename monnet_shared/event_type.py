"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

EventType Constants

"""

class EventType:
    """
    Defines constants representing various event types for monitoring and logging purposes.

    These constants are used to identify different system events such as high resource usage,
    changes in system state, network port status updates, and host discovery events.

    Event Types:
        HIGH_IOWAIT: Event indicating high I/O wait.
        HIGH_MEMORY_USAGE: Event indicating high memory usage.
        HIGH_DISK_USAGE: Event indicating high disk usage.
        HIGH_CPU_USAGE: Event indicating high CPU usage.
        STARTING: (DELETE)
        AGENT_STARTING: Event indicating the agent start.
        AGENT_SHUTDOWN: Event indicating agent shutdown.
        SYSTEM_SHUTDOWN: Event indicating system shutdown.
        PORT_UP: Event indicating a network port is up.
        PORT_DOWN: Event indicating a network port is down.
        PORT_NEW: Event indicating a new network port.
        SEND_STATS: Event indicating that statistics are being sent.
        SERVICE_NAME_CHANGE: Event indicating a change in service name.
        HOST_INFO_CHANGE: Event indicating a change in host information.
        HOST_BECOME_ON: Event indicating the host has become online.
        HOST_BECOME_OFF: Event indicating the host has become offline.
        NEW_HOST_DISCOVERY: Event indicating the discovery of a new host.

    """
    HIGH_IOWAIT = 1
    HIGH_MEMORY_USAGE = 2
    HIGH_DISK_USAGE = 3
    HIGH_CPU_USAGE = 4
    STARTING = 5 # (DELETE)
    AGENT_STARTING = 5
    AGENT_SHUTDOWN = 6
    SYSTEM_SHUTDOWN = 7
    PORT_UP= 8
    PORT_DOWN = 9
    PORT_NEW = 10
    SEND_STATS = 11
    SERVICE_NAME_CHANGE = 12
    HOST_INFO_CHANGE = 13
    HOST_BECOME_ON = 14
    HOST_BECOME_OFF = 15
    NEW_HOST_DISCOVERY = 16
    CERT_ERROR = 17
    PORT_NEW_LOCAL = 18
    PORT_UP_LOCAL = 19
    PORT_DOWN_LOCAL = 20
    TASK_FAILURE = 21
    TASK_SUCCESS = 22
