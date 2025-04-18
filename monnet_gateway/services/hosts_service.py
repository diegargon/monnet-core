"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - HostService Class

"""

# Std
import ipaddress
import json

# Local
from constants.log_type import LogType
from constants.event_type import EventType
from monnet_gateway.database.hosts_model import HostsModel
from monnet_gateway.networking.net_utils import get_hostname, get_mac, get_org_from_mac
from monnet_gateway.services import event_host
from monnet_gateway.services.event_host import EventHostService

from shared.app_context import AppContext
class HostService:
    """Business logic for managing hosts"""

    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.host_model = HostsModel(ctx.get_database())
        self.event_host = EventHostService(ctx)

    def get_all(self) -> list[dict]:
        """Retrieve all hosts with deserialize misc' field."""
        hosts = self.host_model.get_all()
        [self._deserialize_misc(host) for host in hosts]

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

        self._deserialize_misc(host)

        return host

    def add_host(self, host: dict, commit: True) -> int:
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

        try:
            ipaddress.IPv4Address(host["ip"])
        except ValueError:
            raise ValueError(f"Invalid IP address: {host['ip']}")

        #existing_hosts = self.host_model.get_all()
        # check for duplicate MAC warn no error
        #if "mac" in host:
        #    if any(h["mac"] == host["mac"] for h in existing_hosts):
        #        raise ValueError(f"Host with MAC {host['mac']} already exists.")

        self._serialize_misc(host)
        self.host_model.insert_host(host)
        if commit:
            self.host_model.commit()

        last_id = self.host_model.last_id()

        self.event_host.event(
            last_id,
            f'Found new host {host["ip"]} on network {host["network"]}',
            LogType.EVENT_WARN,
            EventType.NEW_HOST_DISCOVERY
        )

        return last_id

    def add_hosts(self, hosts: list[dict]) -> list[int]:
        """
        Add multiple hosts after validating the data.

        Args:
            hosts (list[dict]): List of host data to insert.

        Returns:
            list[int]: List of IDs of the inserted hosts.
        """
        inserted_ids = []

        try:
            for host in hosts:
                # Reutilizar la lógica de add_host sin realizar commit
                inserted_id = self.add_host(host, commit=False)
                inserted_ids.append(inserted_id)
            self.host_model.commit()
        except Exception as e:
            self.logger.error(f"Error inserting hosts: {e}")
            self.host_model.rollback()
            raise ValueError(f"Error inserting hosts: {e}")

        return inserted_ids


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
        # Colect set_data wit missing host detadetails
        self._collect_missing_details(existing_host, set_data)
        # Create events
        self._host_events(existing_host, set_data)
        # Serialize and merge the 'misc' field
        self._serialize_update_misc(existing_host, set_data)
        self.host_model.update_host(host_id, set_data)
        self.host_model.commit()

    def _host_events(self, host: dict, current_host: dict) -> None:
        hid = host["id"]
        ip = host["ip"]

        if host.get("online") == 0 and current_host.get("online") == 1:
            self.event_host.event(
                hid,
                f'Host become online {ip}',
                LogType.EVENT,
                EventType.HOST_BECOME_ON
            )
        if host.get("online") == 1 and current_host.get("online") == 0:
            if "always_on" in host["misc"] and host["misc"]["always_on"]:
                log_type = LogType.EVENT_ALERT
                current_host["alert"] = 1
            else:
                log_type = LogType.EVENT

            self.event_host.event(
                hid,
                f'Host become offline {ip}',
                log_type,
                EventType.HOST_BECOME_ON
            )
        if "hostname" in current_host and host["hostname"] != current_host["hostname"]:
            current_host["warn"] = 1
            self.event_host.event(
                hid,
                f'Host hostname changed {host["hostname"]} -> {current_host["hostname"]}',
                LogType.EVENT_WARN,
                EventType.HOST_INFO_CHANGE
            )
        if "misc" in current_host:
            if "mac" in current_host["misc"] and host["misc"]["mac"] != current_host["misc"]["mac"]:
                current_host["warn"] = 1
                self.event_host.event(
                    hid,
                    f'Host MAC changed {host["misc"]["mac"]} -> {current_host["misc"]["mac"]}',
                    LogType.EVENT_WARN,
                    EventType.HOST_INFO_CHANGE
                )
            if (
                "mac_vendor" in current_host["misc"] and
                host["misc"]["mac_vendor"] != current_host["misc"]["mac_vendor"]
            ):
                self.event_host.event(
                    hid,
                    f'Host MAC vendor changed {host["misc"]["mac_vendor"]} -> {current_host["misc"]["mac_vendor"]}',
                    LogType.EVENT,
                    EventType.HOST_INFO_CHANGE
                )

    def _collect_missing_details(self, existing_host: dict, set_data: dict) -> None:
        """
        Check if the host has missing details and update them if necessary.
        Args:
            existing_host (dict): The existing host data.
            set_data (dict): The new data to be set.
        """
        if not existing_host["hostname"]:
            set_data["hostname"] = get_hostname(existing_host["ip"])
        if "misc" in existing_host:
            if "mac" in existing_host["misc"]:
                set_data["misc"]["mac"] = get_mac(existing_host["ip"])
                if set_data["misc"]["mac"] is not None:
                    set_data["misc"]["mac_vendor"] = get_org_from_mac(set_data["mac"])

    def _serialize_update_misc(self, existing_host: dict,  set_data: dict) -> None:
        """ Handle  update the 'misc' field merge existing and new data """

        if "misc" in set_data:
            if isinstance(set_data["misc"], dict) and set_data["misc"] is not None:
                # Merge the existing 'misc' with the new data
                existing_misc = existing_host.get("misc", {})
                merged_misc = {**existing_misc, **set_data["misc"]}
                try:
                    set_data["misc"] = json.dumps(merged_misc)
                except (TypeError, ValueError) as e:
                    raise ValueError(f"Error serializing 'misc' field to JSON: {e}")
            else:
                raise ValueError("'misc' field must be a dictionary.")

    def _serialize_misc(self, host: dict) -> None:
        """ Serialize the 'misc' field to JSON format."""

        if "misc" in host and isinstance(host["misc"], dict):
            try:
                host["misc"] = json.dumps(host["misc"])
            except (TypeError, ValueError) as e:
                raise ValueError(f"Error serializing 'misc' field to JSON: {e}")

    def _deserialize_misc(self, host: dict) -> None:
        """ Deserialize the 'misc' field from JSON format."""
        if "misc" in host and host["misc"]:
            try:
                host["misc"] = json.loads(host["misc"])
            except (TypeError, ValueError) as e:
                raise ValueError(f"Error deserializing 'misc' field: {e}")
