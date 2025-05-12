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
from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway.database.hosts_model import HostsModel
from monnet_gateway.networking.net_utils import get_hostname, get_mac, get_org_from_mac
from monnet_gateway.services.event_host import EventHostService
from monnet_gateway.services.networks_service import NetworksService


from shared.time_utils import date_now


from shared.app_context import AppContext
class HostService:
    """Business logic for managing hosts"""

    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.config = ctx.get_config()
        self.db = DBManager(self.config)
        self.host_model = HostsModel(self.db)
        self.event_host = EventHostService(ctx)

    def _ensure_db_connection(self) -> None:
        """
        Ensure the database connection is active. Reconnect if necessary.
        """
        try:
            if not self.db.is_connected():
                self.logger.warning("Database connection lost. Reconnecting...")
                self.db.reconnect()
        except Exception as e:
            self.logger.error(f"Failed to reconnect to the database: {e}")
            raise

    def get_all(self) -> list[dict]:
        """Retrieve all hosts with deserialize misc' field."""
        self._ensure_db_connection()
        hosts = self.host_model.get_all()
        for host in hosts:
            if "misc" in host and host["misc"]:
                # Deserialize the 'misc' field
                self._deserialize_misc(host)
            else:
                host["misc"] = {}
            self._set_display_name(host)

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
        self._ensure_db_connection()
        if host_id is None or not isinstance(host_id, int):
            self.logger.warning(f"Invalid host ID in get by id: {host_id}")
            return {}
        host = self.host_model.get_by_id(host_id)
        if not host:
            self.logger.warning(f"Host with ID {host_id} does not exist.")
            return {}
        if "misc" in host and host["misc"]:
            self._deserialize_misc(host)
        else:
            host["misc"] = {}

        self._set_display_name(host)

        return host

    def add_host(self, host: dict, commit: bool = True) -> int:
        """
        Add a new host after validating the data.

        Args:
            host (dict): Host data to insert.
            commit (bool): Whether to commit the transaction. Default is True.

        Returns:
            int: ID of the inserted host.
        """
        self._ensure_db_connection()

        required_fields = ["ip", "network"]
        for field in required_fields:
            if field not in host:
                raise ValueError(f"Missing required field: {field}")

        try:
            ipaddress.IPv4Address(host["ip"])
        except ValueError:
            raise ValueError(f"Invalid IP address: {host['ip']}")
        if "misc" in host and isinstance(host["misc"], dict):
            self._serialize_misc(host)
        self.host_model.insert_host(host)
        if commit:
            self.host_model.commit()

        last_id = self.host_model.last_id()

        self.create_event(
            last_id,
            f'Found new host {host.get("ip")} on network {host.get("network")}',
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
        self._ensure_db_connection()
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
        self._ensure_db_connection()
        if host_id is None or not isinstance(host_id, int):
            self.logger.warning(f"Invalid host ID in update: {host_id}")
            return

        existing_host = self.get_by_id(host_id)
        if existing_host:
            try:
                # display name is not a field in the database is generated on the fly
                if "display_name" in set_data:
                    del set_data["display_name"]
                # Colect set_data wit missing host detadetails
                self._collect_missing_details(existing_host, set_data)
                # Create events
                self._host_events(existing_host, set_data)
                # Serialize and merge the 'misc' field
                if "misc" in set_data:
                    self._serialize_update_misc(existing_host, set_data)
                #self.logger.debug(f"Updating host {host_id} with data: {set_data}")
                self.host_model.update_host(host_id, set_data)
                self.host_model.commit()
            except Exception as e:
                self.logger.error(f"Error updating host {host_id}: {e}")

    def set_alert(self, host_id: int, alarm_status: int) -> None:
        """
        Set the alert status for a host.

        Args:
            host_id (int): ID of the host to update.
            alarm_status (int): New alarm status (0 or 1).
        """
        self._ensure_db_connection()
        if host_id is None or not isinstance(host_id, int):
            self.logger.warning(f"Invalid host ID in set_alarm: {host_id}")
            return
        self.host_model.set_alert(host_id, alarm_status)
        self.host_model.commit()

    def set_warn(self, host_id: int, warn_status: int) -> None:
        """
        Set the warn status for a host.

        Args:
            host_id (int): ID of the host to update.
            warn_status (int): New warn status (0 or 1).
        """
        self._ensure_db_connection()
        if host_id is None or not isinstance(host_id, int):
            self.logger.warning(f"Invalid host ID in set_warn: {host_id}")
            return
        self.host_model.set_warn(host_id, warn_status)
        self.host_model.commit()

    def create_event(self, host_id: int, message: str, log_type: LogType, event_type: EventType) -> None:
        """
        Encapsulate the creation of an event.

        Args:
            host_id (int): ID of the host related to the event.
            message (str): Event message.
            log_type (LogType): Type of log for the event.
            event_type (EventType): Type of event.
        """
        if log_type == LogType.EVENT_WARN:
            self.set_warn(host_id, 1)
        elif log_type == LogType.EVENT_ALERT:
            self.set_alert(host_id, 1)

        self.event_host.event(host_id, message, log_type, event_type)

    def _host_events(self, host: dict, current_host: dict) -> None:
        hid = host.get("id", None)
        ip = host.get("ip", None)

        if ip is None:
            self.logger.warning(f"Host IP is None, cannot create events for host {hid}")
            return
        if hid is None:
            self.logger.warning(f"Host ID is None, cannot create events for host")
            return

        if "misc" in host and isinstance(host["misc"], dict):
            disable_alarms = host.get("misc").get("disable_alarms") == 1
        else:
            disable_alarms = False

        if host.get("online") == 0 and current_host.get("online") == 1:
            current_host["glow"] = date_now()
            self.create_event(
                hid,
                f'Host become online {ip}',
                LogType.EVENT,
                EventType.HOST_BECOME_ON
            )

        if host.get("online") == 1 and current_host.get("online") == 0:
            current_host["glow"] = date_now()
            if disable_alarms or not host.get("misc", {}).get("alway_on"):
                log_type = LogType.EVENT
            else:
                log_type = LogType.EVENT_ALERT
                current_host["alert"] = 1

            self.create_event(
                hid,
                f'Host become offline',
                log_type,
                EventType.HOST_BECOME_OFF
            )

        if "hostname" in current_host and host.get("hostname") != current_host.get("hostname"):
            if disable_alarms or host.get("misc", {}).get("alarm_hostname_disable"):
                log_type = LogType.EVENT
            else:
                current_host["warn"] = 1
                log_type = LogType.EVENT_WARN

            self.create_event(
                hid,
                f'Host hostname changed {host.get("hostname")} -> {current_host.get("hostname")}',
                log_type,
                EventType.HOST_INFO_CHANGE
            )

        if "mac" in current_host and current_host.get("mac") is not None:
            if "mac" not in host or host.get("mac") != current_host.get("mac"):
                if disable_alarms or host.get("misc", {}).get("alarm_macchange_disable"):
                    log_type = LogType.EVENT
                else:
                    current_host["warn"] = 1
                    log_type = LogType.EVENT_WARN

                self.create_event(
                    hid,
                    (
                        f'Host MAC changed {host.get("mac")} -> '
                        f'{current_host.get("mac")}'
                    ),
                    log_type,
                    EventType.HOST_INFO_CHANGE
                )

        if (
            "misc" in host and isinstance(host["misc"], dict) and
            "misc" in current_host and isinstance(current_host["misc"], dict)
        ):

            if (
                "mac_vendor" in current_host["misc"] and
                current_host.get("misc").get("mac_vendor") is not None
            ):
                if (
                    "mac_vendor" not in host["misc"] or
                    host.get("misc").get("mac_vendor") != current_host.get("misc").get("mac_vendor")
                ):
                    self.create_event(
                        hid,
                        (
                            f'Host MAC vendor changed '
                            f'{host.get("misc", {}).get("mac_vendor")} -> '
                            f'{current_host.get("misc").get("mac_vendor")}'
                        ),
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
        ip = existing_host.get("ip", None)
        if ip is None:
            self.logger.warning(f"Host IP is None, cannot collect missing details for host {existing_host.get('id')}")
            return

        if not existing_host.get("hostname"):
            hostname = get_hostname(ip)
            if hostname is not None and isinstance(hostname, str):
                set_data["hostname"] = get_hostname(ip)

        if not existing_host["mac"]:
            mac = get_mac(ip)
            if mac is not None and isinstance(mac, str):
                set_data["mac"] = mac
                mac_vendor = get_org_from_mac(mac)
                if mac_vendor is not None and isinstance(mac_vendor, str):
                    if "misc" not in set_data:
                        set_data["misc"] = {}
                    set_data["misc"]["mac_vendor"] = mac_vendor

    def _serialize_update_misc(self, existing_host: dict,  set_data: dict) -> None:
        """ Handle  update the 'misc' field merge existing and new data """

        if "misc" in set_data:
            if isinstance(set_data["misc"], dict) and set_data["misc"] is not None:
                # Merge the existing 'misc' with the new data
                existing_misc = existing_host.get("misc", {})
                if not isinstance(existing_misc, dict):
                    raise ValueError("'misc' field in existing_host must be a dictionary.")
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
                host["misc"] = json.dumps(host.get("misc"))
            except (TypeError, ValueError) as e:
                raise ValueError(f"Error serializing 'misc' field to JSON: {e}")

    def _deserialize_misc(self, host: dict) -> None:
        """ Deserialize the 'misc' field from JSON format."""
        if "misc" in host and host["misc"]:
            try:
                host["misc"] = json.loads(host.get("misc"))
            except (TypeError, ValueError) as e:
                raise ValueError(f"Error deserializing 'misc' field: {e}")

    def _set_display_name(self, host: dict) -> None:
        """
        Get the display name for a host.

        Args:
            host (dict): The host data.

        Returns:
            str: The display name for the host.
        """

        if "title" in host and host.get("title"):
            host["display_name"] = host.get("title")
        elif "hostname" in host and host.get("hostname"):
            host["display_name"] = host.get("hostname")
        else:
            host["display_name"] = host.get("ip")

    def get_hosts_not_seen(self, days: int) -> list[dict]:
        """
        Get hosts that have not been seen for more than the specified number of days.

        Args:
            days (int): Number of days.

        Returns:
            list[dict]: List of hosts not seen for more than the specified days.
        """
        if days <= 0:
            raise ValueError("Days must be a positive integer.")
        self._ensure_db_connection()

        return self.host_model.get_hosts_not_seen_for_days(days)

    def delete_hosts_by_ids(self, host_ids: list[int]) -> int:
        """
        Delete hosts by a list of IDs.

        Args:
            host_ids (list[int]): List of host IDs to delete.

        Returns:
            int: Number of hosts deleted.
        """
        if not host_ids:
            self.logger.warning("No host IDs provided for deletion.")
            return 0
        self._ensure_db_connection()
        deleted_count = self.host_model.delete_hosts_by_ids(host_ids)
        self.host_model.commit()
        self.logger.info(f"Purged {deleted_count} hosts with IDs: {host_ids}")
        return deleted_count

    def clear_not_seen_hosts(self, days: int) -> int:
        """
        Clear hosts that have not been seen for more than the specified number of days,
        filtered by networks with `clear=1`.

        Args:
            days (int): Number of days.

        Returns:
            int: Number of hosts cleared.
        """
        if days <= 0:
            raise ValueError("Days must be a positive integer.")
        self._ensure_db_connection()

        # Instantiate NetworksService
        networks_service = NetworksService(self.ctx)

        # Get networks with `clear=1`
        networks_to_clear = networks_service.get_networks_for_clear()

        if not networks_to_clear:
            self.logger.debug("No networks with `clean=1` found.")
            return 0

        # Extract network IDs
        network_ids = [network["id"] for network in networks_to_clear]

        # Get hosts not seen for the specified number of days in these networks
        hosts_to_clear = self.host_model.get_hosts_not_seen_in_networks(days, network_ids)
        host_ids = [host["id"] for host in hosts_to_clear]

        if not host_ids:
            self.logger.debug(f"No hosts found not seen for more than {days} days in the specified networks.")
            return 0

        # Delete the hosts
        deleted_count = self.delete_hosts_by_ids(host_ids)
        self.logger.notice(f"Cleared {deleted_count} hosts not seen for more than {days} days.")

        return deleted_count
