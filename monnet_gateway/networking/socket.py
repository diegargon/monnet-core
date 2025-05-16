"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""
# Std
import socket
from typing import Optional, Tuple

# Local
from monnet_shared.app_context import AppContext


class SocketHandler:
    def __init__(self, timeout: float = 5.0):
        """
        Sockets (TCP/UDP).

        Args:
            timeout: Sockets timeout in seconds
        """
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self.connection: Optional[socket.socket] = None  # Para sockets TCP (modo servidor)
        self.client_address: Optional[Tuple[str, int]] = None  # Para sockets TCP (modo servidor)

    def create_tcp_socket(self, family: int = socket.AF_INET) -> bool:
        """Crea un socket TCP."""
        try:
            self.socket = socket.socket(family, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            return True
        except OSError as e:
            raise OSError(f"Failed to create TCP socket: {e}")

    def create_udp_socket(self) -> bool:
        """Crea un socket UDP."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(self.timeout)
            return True
        except OSError as e:
            raise OSError(f"Failed to create UDP socket: {e}")

    def bind(self, host: str, port: int) -> bool:
        """Enlaza el socket a una dirección y puerto específicos."""

        if not isinstance(host, str) or not isinstance(port, int):
            raise RuntimeError("Invalid host or port")

        if not self.socket:
            raise RuntimeError("Socket not created")

        try:
            self.socket.bind((host, port))
            return True
        except OSError as e:
            raise OSError(f"Failed to bind socket to {host}:{port}: {e}")

    def tcp_listen(self, backlog: int = 5) -> bool:
        """Pone el socket TCP en modo escucha."""
        if not self._validate_socket(socket.SOCK_STREAM):
            return False

        try:
            self.socket.listen(backlog)
            return True
        except Exception as e:
            raise ConnectionError(f"Error listening on TCP socket: {e}")

    def tcp_accept(self) -> bool:
        """Acepta una conexión entrante (TCP)."""
        if not self._validate_socket(socket.SOCK_STREAM):
            return False

        try:
            self.connection, self.client_address = self.socket.accept()
            self.connection.settimeout(self.timeout)
            return True
        except socket.timeout:
            raise ConnectionError("Timeout waiting for connection")
        except Exception as e:
            raise ConnectionError(f"Error accepting connection: {e}")
            return False

    def tcp_connect(self, host: str, port: int) -> bool:
        """Establece una conexión TCP con un servidor."""
        if not self._validate_socket(socket.SOCK_STREAM):
            raise RuntimeError("Socket is not valid or not created")

        try:
            resolved_host = self.resolve_host(host)
            self.socket.connect((resolved_host, port))
            return True
        except socket.timeout:
            raise ConnectionError(f"Connection to {host}:{port} timed out")
        except OSError as e:
            raise ConnectionError(f"Failed to connect to {host}:{port}: {e}")

    def resolve_host(self, host: str) -> str:
        """Resuelve un dominio a una dirección IP."""
        try:
            return socket.gethostbyname(host)
        except socket.gaierror as e:
            raise RuntimeError(f"Failed to resolve host {host}: {e}")

    def send(self, data: bytes, address: Optional[Tuple[str, int]] = None) -> bool:
        """
        Envía datos a través del socket.

        Para TCP: no se especifica address (usa conexión establecida)
        Para UDP: se debe especificar address (host, port)
        """

        try:
            if self.socket.type == socket.SOCK_STREAM:
                if not self._validate_socket(socket.SOCK_STREAM, check_connection=True):
                    return False
                self.connection.sendall(data)
            else:
                if not self._validate_socket(socket.SOCK_DGRAM):
                    return False
                if not address:
                    raise ValueError("UDP send requires a destination address")
                self.socket.sendto(data, address)
            return True
        except socket.timeout:
            raise ConnectionError("Socket operation timed out")
        except OSError as e:
            raise ConnectionError(f"Socket error: {e}")
        except Exception as e:
            raise ConnectionError(f"Unexpected error socket sending: {e}")

    def receive(self, buffer_size: int = 4096) -> Tuple[Optional[bytes], Optional[Tuple[str, int]]]:
        """
        Recibe datos del socket.

        Returns:
            Tuple (data, address)
            - Para TCP: address None
            - Para UDP: address hold(host, port) from remitente
        """
        if not isinstance(buffer_size, int) or buffer_size <= 0:
            raise RuntimeError("Buffer size must be a positive integer")
        try:
            if self.socket.type == socket.SOCK_STREAM:
                if not self._validate_socket(socket.SOCK_STREAM):
                    return None, None
                data = self.connection.recv(buffer_size)
                if not data:
                    raise ConnectionError("Connection closed by peer")

                return data, None
            else:
                if not self._validate_socket(socket.SOCK_DGRAM):
                    return None, None
                data, address = self.socket.recvfrom(buffer_size)

                return data, address
        except socket.timeout:
            raise ConnectionError("Socket operation timed out")
        except OSError as e:
            raise ConnectionError(f"Failed to receive data: {e}")

    def close(self) -> None:
        """Cierra el socket y cualquier conexión asociada."""
        if self.connection:
            try:
                self.connection.close()
            except OSError as e:
                raise RuntimeError(f"Error closing connection: {e}")
            finally:
                self.connection = None

        if self.socket:
            try:
                self.socket.close()
            except OSError as e:
                raise RuntimeError(f"Error closing socket: {e}")
            finally:
                self.socket = None

    def set_timeout(self, timeout: float):
        """ Set Socket Timeout """
        self.timeout = timeout
        if self.socket:
            self.socket.settimeout(timeout)
        if self.connection:
            self.connection.settimeout(timeout)

    def _validate_socket(self, expected_type: int, check_connection: bool = False) -> bool:
        """Valida el socket y, opcionalmente, la conexión activa."""
        if not self.socket:
            raise RuntimeError("Socket not created")
        if self.socket.type != expected_type:
            raise RuntimeError(f"Invalid socket type. Expected {expected_type}, got {self.socket.type}")
        if check_connection and not self.connection:
            raise RuntimeError("No active TCP connection")

        return True

    def __del__(self):
        """Destructor que asegura que los sockets se cierren."""
        self.close()
