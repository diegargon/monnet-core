"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent - Requests
"""

import uuid
from monnet_agent import agent_config, info_linux
from monnet_shared import time_utils
from monnet_shared.app_context import AppContext


def get_meta(ctx: AppContext):
    """
    Build metadata.

    Args:
        ctx (AppContext): Context.
    Returns:
        dict: Dictionary with metadata.
    """

    timestamp = time_utils.date_now()
    local_timezone = time_utils.get_local_timezone()
    hostname = info_linux.get_hostname()
    nodename = info_linux.get_nodename()
    if hostname:
        ip_address = info_linux.get_ip_address(hostname)
    else:
        ip_address = None

    _uuid = str(uuid.uuid4())

    meta = {
        "timestamp": timestamp,                       # Timestamp  UTC
        "timezone": str(local_timezone),              # Timezone
        "hostname": hostname,
        "nodename": nodename,
        "ip_address": ip_address,
        "agent_version": str(agent_config.AGENT_VERSION),
        "uuid": _uuid                                 # ID uniq
    }
    # log(f"Metadata: {meta}", "debug")
    return meta
