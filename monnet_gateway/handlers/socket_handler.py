"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""
# Std
import socket

# Local
from shared.app_context import AppContext

class SocketHandler:
    def __init__(self, ctx: AppContext, timeout_sec=0, timeout_usec=100000):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.timeout_sec = timeout_sec
        self.timeout_usec = timeout_usec
        self.socket = None

    def create_socket(self):
        """Crea un socket RAW para ICMP."""
        try:
            protocol_number = socket.getprotobyname('icmp')
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, protocol_number)
            self.socket.settimeout(self.timeout_sec + self.timeout_usec / 1000000)
        except Exception as e:
            self.logger.error(f"Error creating socket: {e}")
            return False
        return True

    def is_icmp_socket(self):
        """Verifica si el socket está configurado para ICMP."""
        try:
            protocol_number = socket.getprotobyname('icmp')
            return self.socket and self.socket.proto == protocol_number
        except Exception as e:
            self.logger.error(f"Error verifying ICMP socket: {e}")
            return False

    def send_packet(self, ip: str, packet):
        """Envía un paquete a la IP especificada."""
        try:
            if (not self.socket):
                self.logger.error("Socket is not created or not valid")
                return False
            self.socket.sendto(packet, (ip, 0))
        except Exception as e:
            self.logger.error(f"Error sending packet to {ip}: {e}")
            return False
        return True

    def receive_packet(self, buffer_size=1024):
        """Recibe un paquete desde el socket."""
        try:
            #self.logger.debug("Waiting to receive a packet...")
            buffer, from_ip = self.socket.recvfrom(buffer_size)
            self.logger.debug(f"Packet received from {from_ip} with size {len(buffer)} bytes")
            self.logger.debug(f"Raw packet data: {buffer.hex()}")

            # Validar que el paquete tenga al menos un encabezado IP completo
            if len(buffer) < 20:
                self.logger.warning(f"Received packet too small to contain valid IP header (size: {len(buffer)})")
                return None, None

            # Verificar si el paquete es ICMP
            #ip_header = buffer[:20]
            #src_ip = socket.inet_ntoa(ip_header[12:16])
            #self.logger.debug(f"Source IP from IP header: {src_ip}")
            #self.logger.debug(f"Socket returned from_addr: {from_ip[0]}")

            return buffer, from_ip[0]
        except socket.timeout:
            self.logger.warning("Socket timed out while waiting for a packet")
            return None, None
        except Exception as e:
            self.logger.error(f"Error receiving packet: {e}")
            self.close_socket()
            return None, None

    def close_socket(self):
        """Cierra el socket."""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                self.logger.error(f"Error closing socket: {e}")
            finally:
                self.socket = None