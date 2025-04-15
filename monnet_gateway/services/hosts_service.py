"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - HostService Class

"""

import json
from monnet_gateway.database.hosts_model import HostsModel
from shared.app_context import AppContext


class HostService:
    """Business logic for managing hosts"""

    def __init__(self, ctx: AppContext, host_model: HostsModel):
        self.ctx = ctx
        self.host_model = host_model

    def get_all(self) -> list[dict]:
        """Retrieve all hosts and convert """
        hosts = self.host_model.get_all()
        for host in hosts:
            if "misc" in host and host["misc"]:
                try:
                    host["misc"] = json.loads(host["misc"])
                except (TypeError, ValueError) as e:
                    raise ValueError(f"Error deserializing 'misc' field for host {host['ip']}: {e}")
        return hosts

    def add_host(self, host: dict) -> int:
        """
        Add a new host after validating the data.

        Args:
            host (dict): Host data to insert.

        Returns:
            int: ID of the inserted host.
        """
        # Validate required fields
        required_fields = ["ip", "network"]
        for field in required_fields:
            if field not in host:
                raise ValueError(f"Missing required field: {field}")

        # check for duplicate MAC
        existing_hosts = self.host_model.get_all()
        if "mac" in host:
            if any(h["mac"] == host["mac"] for h in existing_hosts):
                raise ValueError(f"Host with MAC {host['mac']} already exists.")

        if "misc" in host and isinstance(host["misc"], dict):
            try:
                host["misc"] = json.dumps(host["misc"])
            except (TypeError, ValueError) as e:
                raise ValueError(f"Error serializing 'misc' field to JSON: {e}")

        # Insert the host into the database
        return self.host_model.insert_host(host)