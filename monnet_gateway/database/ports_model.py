"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Ports Model

"""

from monnet_gateway.database.dbmanager import DBManager


class PortsModel:
    """
    Handles operations related to the `ports` table.

    The `ports` table structure:
    - `id` (Primary, int, AUTO_INCREMENT): Unique identifier for each port entry.
    - `hid` (Index, int): Host ID associated with the port.
    - `scan_type` (tinyint): 1 Remote , 2 agent.
    - `protocol` (char(10)): Protocol used by the port (e.g., TCP, UDP or HTTPs conn).
    - `pnumber` (int): Port number.
    - `online` (tinyint): Online status of the port (0 = offline, 1 = online).
    - `interface` (varchar(255)): Network interface associated with the port.
    - `ip_version` (tinyint): IP version (4 for IPv4, 6 for IPv6).
    - `custom_service` (varchar(255)): Custom service name associated with the port.
    - `service` (varchar(255)): Detected service name running on the port.
    - `latency` (int): Latency in milliseconds.
    - `last_change` (datetime): Timestamp of the last status change.
    """

    def __init__(self, db: DBManager):
        """
        Initialize PortsModel with a database manager.
        Args:
            db: Database manager instance.
        """
        self.db = db

    def add(self, port_data: dict) -> int:
        """
        Add a new port entry to the database.
        Args:
            port_data (dict): Dictionary containing port details.
        Returns:
            int: ID of the newly added port.
        """
        # Filtrar solo los campos presentes en port_data
        valid_fields = {
            "hid", "scan_type", "protocol", "pnumber", "online", "interface",
            "ip_version", "custom_service", "service", "latency", "last_change"
        }
        filtered_data = {key: value for key, value in port_data.items() if key in valid_fields}
        return self.db.insert("ports", filtered_data)

    def update(self, port_id: int, port_data: dict) -> None:
        """
        Update an existing port entry in the database.
        Args:
            port_id (int): ID of the port to update.
            port_data (dict): Dictionary containing updated port details.
        """
        # Filtrar solo los campos presentes en port_data
        valid_fields = {
            "hid", "scan_type", "protocol", "pnumber", "online", "interface",
            "ip_version", "custom_service", "service", "latency", "last_change"
        }
        filtered_data = {key: value for key, value in port_data.items() if key in valid_fields}
        self.db.update("ports", filtered_data, {"id": port_id})

    def add_ports(self, ports_data: list[dict]) -> list[int]:
        """
        Add multiple port entries to the database.
        Args:
            ports_data (list[dict]): List of dictionaries containing port details.
        Returns:
            list[int]: List of IDs of the newly added ports.
        """
        valid_fields = {
            "hid", "scan_type", "protocol", "pnumber", "online", "interface",
            "ip_version", "custom_service", "service", "latency", "last_change"
        }
        inserted_ids = []
        with self.db.transaction():
            for port_data in ports_data:
                filtered_data = {key: value for key, value in port_data.items() if key in valid_fields}
                inserted_id = self.db.insert("ports", filtered_data)
                inserted_ids.append(inserted_id)

        return inserted_ids

    def update_ports(self, ports_data: list[dict]) -> None:
        """
        Update multiple port entries in the database.
        Args:
            ports_data (list[dict]): List of dictionaries containing port details.
        """
        valid_fields = {
            "hid", "scan_type", "protocol", "pnumber", "online", "interface",
            "ip_version", "custom_service", "service", "latency", "last_change"
        }
        for port_data in ports_data:
            if "id" not in port_data:
                raise ValueError("Each port_data must include an 'id' field for updates.")
            port_id = port_data["id"]
            filtered_data = {key: value for key, value in port_data.items() if key in valid_fields}
            self.db.update("ports", filtered_data, {"id": port_id})

    def get_all(self, scan_type: int = None) -> list[dict]:
        """
        Retrieve all port entries from the database.
        Args:
            scan_type (int, optional): Filter by scan_type. Defaults to None (retrieve all).
        Returns:
            list[dict]: List of port entries.
        """
        query = "SELECT * FROM ports"
        params = {}
        if scan_type is not None:
            query += " WHERE scan_type = %(scan_type)s"
            params['scan_type'] = scan_type
        return self.db.fetchall(query, params)

    def get_by_id(self, port_id: int, scan_type: int = None) -> dict:
        """
        Retrieve a port entry by its ID.
        Args:
            port_id (int): ID of the port to retrieve.
            scan_type (int, optional): Filter by scan_type. Defaults to None (retrieve all).
        Returns:
            dict: Port entry details.
        """
        query = "SELECT * FROM ports WHERE id = %(id)s"
        params = {'id': port_id}
        if scan_type is not None:
            query += " AND scan_type = %(scan_type)s"
            params['scan_type'] = scan_type

        return self.db.fetchone(query, params)

    def get_by_hid(self, hid: int, scan_type: int = None) -> list[dict]:
        """
        Retrieve port entries by host ID (hid).
        Args:
            hid (int): Host ID to filter by.
            scan_type (int, optional): Filter by scan_type. Defaults to None (retrieve all).
        Returns:
            list[dict]: List of port entries for the specified host ID.
        """
        query = "SELECT * FROM ports WHERE hid = %(hid)s"
        params = {'hid': hid}
        if scan_type is not None:
            query += " AND scan_type = %(scan_type)s"
            params['scan_type'] = scan_type

        return self.db.fetchall(query, params)

    def commit(self) -> None:
        self.db.commit()