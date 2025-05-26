"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - AgentsCheckTask

# TODO: if agent_online=0 ping host
# TODO: last_seen no es fiable por que lo pone ping tambien, comprobar con ¿agent_last_seen?
"""

from time import time
from monnet_gateway.services.hosts_service import HostService
from monnet_shared.app_context import AppContext
from monnet_shared.time_utils import utc_date_now
from datetime import datetime, timezone

class AgentsCheckTask:
    """Check agent_installed hosts and update agent_online if last_seen > 60s"""
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.config = ctx.get_config()

    def run(self):
        host_service = HostService(self.ctx)
        now = int(time())
        updated = 0

        try:
            agent_interval = int(self.config.get("agent_default_interval", 60))
        except Exception:
            agent_interval = 60

        agent_interval += 10  # Add grace period to avoid false positives

        # Get all hosts with agent_installed
        hosts = host_service.get_agent_installed_hosts()
        for host in hosts:
            last_seen = host.get("last_seen")
            if last_seen is None:
                self.logger.notice(f"AgentsCheckTask: Host {host['id']} has no last_seen timestamp, skipping.")
                continue
            if not isinstance(last_seen, datetime):
                self.logger.error(f"AgentsCheckTask: last_seen for host {host['id']} is not a datetime: {last_seen}")
                continue
            # Pone tzinfo a UTC si no last_seen.timestamp() asume que es local
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            else:
                last_seen = last_seen.astimezone(timezone.utc)
            last_seen_ts = int(last_seen.timestamp())
            seconds_since_last_seen = now - last_seen_ts
            if seconds_since_last_seen > agent_interval:
                if host.get("agent_online") != 0:
                    host_service.update(
                        host["id"],
                        {
                            "agent_online": 0,
                            "last_check": utc_date_now()
                        }
                    )
                    self.logger.notice(
                        f"AgentsCheckTask: Host offline {host.get('hostname')} ({host.get('ip')}), "
                        f"last_seen {seconds_since_last_seen} seconds ago"
                    )
                    updated += 1
        if updated:
            self.logger.info(f"AgentsCheckTask: Set agent_online=0 for {updated} hosts.")
