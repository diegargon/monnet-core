"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""
# Std
import socket
from typing import Optional, Tuple

# Local
from shared.app_context import AppContext


class SocketHandler:
    def __init__(self, ctx: AppContext, timeout: float = 5.0):
        """
        Sockets (TCP/UDP).

        Args:
            ctx: Contexto
            timeout: Sockets timeout in seconds
        """
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self.connection: Optional[socket.socket] = None  # Para sockets TCP (modo servidor)
        self.client_address: Optional[Tuple[str, int]] = None  # Para sockets TCP (modo servidor)

    def create_tcp_socket(self) -> bool:
        """Crea un socket TCP."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            return True
        except Exception as e:
            self.logger.error(f"Error creating TCP socket: {e}")
            return False

    def create_udp_socket(self) -> bool:
        """Crea un socket UDP."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(self.timeout)
            return True
        except Exception as e:
            self.logger.error(f"Error creating UDP socket: {e}")
            return False

    def bind(self, host: str, port: int) -> bool:
        """Enlaza el socket a una dirección y puerto específicos."""
        if not self.socket:
            self.logger.error("Socket not created")
            return False

        try:
            self.socket.bind((host, port))
            self.logger.info(f"Socket bound to {host}:{port}")
            return True
        except Exception as e:
            self.logger.error(f"Error binding socket to {host}:{port}: {e}")
            return False

    def tcp_listen(self, backlog: int = 5) -> bool:
        """Pone el socket TCP en modo escucha."""
        if not self.socket or self.socket.type != socket.SOCK_STREAM:
            self.logger.error("Not a TCP socket or socket not created")
            return False

        try:
            self.socket.listen(backlog)
            self.logger.info(f"TCP socket listening with backlog {backlog}")
            return True
        except Exception as e:
            self.logger.error(f"Error listening on TCP socket: {e}")
            return False

    def tcp_accept(self) -> bool:
        """Acepta una conexión entrante (TCP)."""
        if not self.socket or self.socket.type != socket.SOCK_STREAM:
            self.logger.error("Not a TCP socket or socket not created")
            return False

        try:
            self.connection, self.client_address = self.socket.accept()
            self.connection.settimeout(self.timeout)
            self.logger.info(f"Accepted connection from {self.client_address}")
            return True
        except socket.timeout:
            self.logger.warning("Timeout waiting for connection")
            return False
        except Exception as e:
            self.logger.error(f"Error accepting connection: {e}")
            return False

    def tcp_connect(self, host: str, port: int) -> bool:
        """Establece una conexión TCP con un servidor."""
        if not self.socket or self.socket.type != socket.SOCK_STREAM:
            self.logger.error("Not a TCP socket or socket not created")
            return False

        try:
            self.socket.connect((host, port))
            self.logger.info(f"Connected to {host}:{port}")
            return True
        except Exception as e:
            self.logger.error(f"Error connecting to {host}:{port}: {e}")
            return False

    def send(self, data: bytes, address: Optional[Tuple[str, int]] = None) -> bool:
        """
        Envía datos a través del socket.

        Para TCP: no se especifica address (usa conexión establecida)
        Para UDP: se debe especificar address (host, port)
        """
        try:
            if self.socket.type == socket.SOCK_STREAM:
                if not (self.socket or self.connection):
                    self.logger.error("No active TCP connection")
                    return False

                target = self.connection if self.connection else self.socket
                target.sendall(data)
            else:
                if not address:
                    self.logger.error("UDP send requires destination address")
                    return False
                self.socket.sendto(data, address)

            return True
        except Exception as e:
            self.logger.error(f"Error sending data: {e}")
            return False

    def receive(self, buffer_size: int = 4096) -> Tuple[Optional[bytes], Optional[Tuple[str, int]]]:
        """
        Recibe datos del socket.

        Returns:
            Tuple (data, address)
            - Para TCP: address None
            - Para UDP: address hold(host, port) from remitente
        """
        try:
            if self.socket.type == socket.SOCK_STREAM:
                if not (self.socket or self.connection):
                    self.logger.error("No active TCP connection")
                    return None, None

                target = self.connection if self.connection else self.socket
                data = target.recv(buffer_size)
                if not data:
                    self.logger.warning("Connection closed by peer")
                    return None, None
                return data, None
            data, address = self.socket.recvfrom(buffer_size)
            return data, address

        except socket.timeout:
            current_timeout = self.socket.gettimeout()  # self.socket es tu socket
            self.logger.warning(f"Socket timeout ({current_timeout} segundos) while receiving data")
            return None, None
        except Exception as e:
            self.logger.error(f"Error receiving data: {e}")
            return None, None

    def close(self):
        """Cierra el socket y cualquier conexión asociada."""
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                self.logger.error(f"Error closing connection: {e}")
            finally:
                self.connection = None
                self.client_address = None

        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                self.logger.error(f"Error closing socket: {e}")
            finally:
                self.socket = None

    def set_timeout(self, timeout: float):
        """Establece un nuevo timeout para el socket."""
        self.timeout = timeout
        if self.socket:
            self.socket.settimeout(timeout)
        if self.connection:
            self.connection.settimeout(timeout)

    def __del__(self):
        """Destructor que asegura que los sockets se cierren."""
        self.close()
