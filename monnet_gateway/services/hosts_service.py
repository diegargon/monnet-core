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

    def get_by_id(self, host_id: int) -> dict:
        """
        Retrieve a host by its ID and deserialize the 'misc' field.

        Args:
            host_id (int): ID of the host to retrieve.

        Returns:
            dict: A dictionary representing the host with 'misc' deserialized.

        Raises:
            ValueError: If the host does not exist.
        """
        host = self.host_model.get_by_id(host_id)
        if not host:
            raise ValueError(f"Host with ID {host_id} does not exist.")

        # Deserialize the 'misc' field if it exists
        if "misc" in host and host["misc"]:
            try:
                host["misc"] = json.loads(host["misc"])
            except (TypeError, ValueError) as e:
                raise ValueError(f"Error deserializing 'misc' field for host {host_id}: {e}")

        return host

    def insert(self, host: dict) -> int:
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


        #existing_hosts = self.host_model.get_all()
        # check for duplicate MAC warn no error
        #if "mac" in host:
        #    if any(h["mac"] == host["mac"] for h in existing_hosts):
        #        raise ValueError(f"Host with MAC {host['mac']} already exists.")

        if "misc" in host and isinstance(host["misc"], dict):
            try:
                host["misc"] = json.dumps(host["misc"])
            except (TypeError, ValueError) as e:
                raise ValueError(f"Error serializing 'misc' field to JSON: {e}")

        return self.host_model.insert_host(host)

    def update(self, host_id: int, set_data: dict) -> None:
        """
        Update an existing host with the provided data.

        Args:
            host_id (int): ID of the host to update.
            set_data (dict): Dictionary containing the fields to update.

        Raises:
            ValueError: If the host does not exist or if there are validation errors.
        """

        existing_host = self.get_by_id(host_id)

        # Handle the 'misc' field: merge existing and new data
        if "misc" in set_data:
            if isinstance(set_data["misc"], dict):
                # Merge the existing 'misc' with the new data
                existing_misc = existing_host.get("misc", {})
                merged_misc = {**existing_misc, **set_data["misc"]}
                try:
                    set_data["misc"] = json.dumps(merged_misc)
                except (TypeError, ValueError) as e:
                    raise ValueError(f"Error serializing 'misc' field to JSON: {e}")
            else:
                raise ValueError("'misc' field must be a dictionary.")

        self.host_model.update_host(host_id, set_data)
