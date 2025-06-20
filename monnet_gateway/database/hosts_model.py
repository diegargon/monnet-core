"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Hosts Model

"""

from monnet_gateway.database.dbmanager import DBManager

class HostsModel:
    """
    DB Operations to manage hosts.

    The `hosts` table structure:
    - `id` (Primary, int, AUTO_INCREMENT): Unique identifier for each host.
    - `title` (char(32), nullable): Title or name of the host.
    - `hostname` (varchar(1024), nullable): Hostname of the host.
    - `ip` (char(18), unique): IP address of the host.
    - `category` (int): Category of the host (default is 1).
    - `mac` (char(17), nullable): MAC address of the host.
    - `highlight` (tinyint(1)): Highlight status (default is 0).
    - `check_method` (tinyint): Method to check the host (1: ping, 2: TCP ports, 3: HTTPS).
    - `weight` (tinyint): Weight of the host (default is 60).
    - `online` (tinyint): Online status of the host (default is 0).
    - `glow` (datetime): Track Last glow timestamp (default is CURRENT_TIMESTAMP).
    - `online_change` (datetime): Track Last online status change timestamp (default is CURRENT_TIMESTAMP).
    - `disable` (tinyint): Disable status (default is 0).
    - `warn` (tinyint): Warning status (default is 0).
    - `warn_mail` (tinyint(1)): Warning email status (default is 0).
    - `scan` (tinyint): Unused field (default is 0).
    - `alert` (tinyint): Alert status (default is 0).
    - `network` (tinyint): Network ID (default is 1).
    - `updated` (datetime): Last updated timestamp (default is CURRENT_TIMESTAMP).
    - `created` (datetime): Creation timestamp (default is CURRENT_TIMESTAMP).
    - `token` (char(255), nullable): Token associated with the host.
    - `notes_id` (int, nullable): Notes ID associated with the host.
    - `encrypted` (text, nullable): Encrypted data related to the host.
    - `last_check` (datetime, nullable): Last check timestamp.
    - `misc` (json, nullable): Miscellaneous data in JSON format.
    - `ansible_enabled` (tinyint): Ansible enabled status (default is 0).
    - `ansible_fail` (tinyint): Ansible failure status (default is 0).
    - `agent_installed` (tinyint(1)): Agent installation status (default is 0).
    - `agent_online` (tinyint(1)): Agent online status (default is 0).
    - `linked` (int, nullable): Linked host ID (default is 0).
    - `rol` (int, nullable): Host role ID (default is 0).
    """

    def __init__(self, db: DBManager):
        self.db = db

    def get_all(self) -> list[dict]:
        """ Get all hosts """
        return self.db.fetchall("SELECT * FROM hosts")

    def get_all_enabled(self) -> list[dict]:
        """ Get all hosts enabled """
        return self.db.fetchall("SELECT * FROM hosts WHERE disable = 0")

    def get_by_id(self, host_id: int) -> dict:
        """
        Retrieve a host by its ID.

        Args:
            host_id (int): ID of the host to retrieve.

        Returns:
            dict: A dictionary representing the host, or None if not found.
        """
        query = "SELECT * FROM hosts WHERE id = %s"

        return self.db.fetchone(query, (host_id,))

    def insert_host(self, host: dict) -> int:
        """ Insert a new host """
        columns = ", ".join(host.keys())
        placeholders = ", ".join(["%s"] * len(host))
        values = tuple(host.values())
        query = f"INSERT INTO hosts ({columns}) VALUES ({placeholders})"

        return self.db.execute(query, values)

    def update_host(self, host_id: int, set_data: dict) -> int:
        """
        Update an existing host in the database.

        Args:
            host_id (int): ID of the host to update.
            set_data (dict): Dictionary containing the fields to update.

        Raises:
            ValueError: If set_data is empty.
        """
        if not set_data:
            raise ValueError("No data provided to update the host.")

        columns = ", ".join([f"{key} = %s" for key in set_data.keys()])
        values = tuple(set_data.values())
        query = f"UPDATE hosts SET {columns} WHERE id = %s"

        return self.db.execute(query, values + (host_id,))


    def last_id(self) -> int:
        """ Get last inserted id """
        return self.db.cursor.lastrowid

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def set_alert(self, host_id: int, alarm_status: int) -> None:
        """
        Set the aklert status for a host.

        Args:
            host_id (int): ID of the host to update.
            alarm_status (int): New alarm status (0 or 1).
        """
        self.db.update("hosts", {"alert": alarm_status}, {"id": host_id})

    def set_warn(self, host_id: int, warn_status: int) -> None:
        """
        Set the warn status for a host.

        Args:
            host_id (int): ID of the host to update.
            warn_status (int): New warn status (0 or 1).
        """
        self.db.update("hosts", {"warn": warn_status}, {"id": host_id})

    def get_hosts_not_seen(self, days: int) -> list[dict]:
        """
        Get hosts that have not been seen for more than the specified number of days.

        Args:
            days (int): Number of days.

        Returns:
            list[dict]: List of hosts not seen for more than the specified days.
        """
        query = """
            SELECT * FROM hosts
            WHERE last_seen IS NOT NULL AND last_seen != 0
              AND last_seen < NOW() - INTERVAL %s DAY
        """
        return self.db.fetchall(query, (days,))

    def delete_hosts_by_ids(self, host_ids: list[int]) -> int:
        """
        Delete hosts by a list of IDs.

        Args:
            host_ids (list[int]): List of host IDs to delete.

        Returns:
            int: Number of rows deleted.
        """
        if not host_ids:
            return 0
        query = "DELETE FROM hosts WHERE id IN (%s)" % ",".join(["%s"] * len(host_ids))
        return self.db.execute(query, tuple(host_ids))

    def get_hosts_not_seen_in_networks(self, days: int, network_ids: list[int]) -> list[dict]:
        """
        Get hosts that have not been seen for more than the specified number of days
        and belong to the specified networks.

        Args:
            days (int): Number of days.
            network_ids (list[int]): List of network IDs.

        Returns:
            list[dict]: List of hosts not seen for more than the specified days in the given networks.
        """
        if not network_ids:
            return []

        placeholders = ",".join(["%s"] * len(network_ids))
        query = f"""
            SELECT id FROM hosts
            WHERE last_seen < NOW() - INTERVAL %s DAY
            AND network IN ({placeholders})
        """

        return self.db.fetchall(query, [days] + network_ids)

    def get_agent_installed_hosts(self) -> list[dict]:
        """
        Get all hosts where agent_installed=1.

        Returns:
            list[dict]: List of hosts with agent_installed=1.
        """
        return self.db.fetchall("SELECT * FROM hosts WHERE agent_installed = 1")
