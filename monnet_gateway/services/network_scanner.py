"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Network Scanner

"""
# Std
import ipaddress
import random
import struct
from time import time

# Third party
import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Local
from monnet_gateway.database.hosts_model import HostsModel
from monnet_gateway.database.networks_model import NetworksModel
from monnet_gateway.networking.socket_raw import SocketRawHandler
from monnet_gateway.networking.socket import SocketHandler
from monnet_gateway.networking.icmp_packet import ICMPPacket
from monnet_shared.app_context import AppContext

class NetworkScanner:
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = self.ctx.get_logger()

    def get_discovery_ips(self, networks_model: NetworksModel, host_model: HostsModel) -> list[str]:
        """
        Get the list of IPs to be scanned
        :return: list of IPs
        """
        ip_list = self.build_ip_list(networks_model)
        logger = self.ctx.get_logger()

        if not ip_list:
            logger.error("No IPs to scan")
            return []

        all_known_hosts = host_model.get_all() or []

        host_ips = {host['ip'] for host in all_known_hosts}
        ip_list = [ip for ip in ip_list if ip not in host_ips]

        return ip_list

    def build_ip_list(self, networks_model: NetworksModel) -> list[str]:
        ip_list = []
        networks = networks_model.get_all()

        if not networks:
            self.logger.notice("No networks found to scan")
            return ip_list

        for net in networks:
            if net.get('disable') == 1 or net.get('scan') != 1:
                self.logger.debug(f"Skipping due flags: {net}")
                continue

            if 'network' not in net:
                self.logger.error("Missing 'network' key in network entry")
                continue

            network_str = net.get('network')
            if not network_str or not self.is_valid_network(network_str):
                self.logger.error(f"Invalid network detected {network_str}")
                continue

            if network_str.startswith("0"):
                continue

            self.logger.debug(f"Pinging networks {net}")

            try:
                network = ipaddress.IPv4Network(network_str, strict=False)
            except ValueError:
                self.logger.error("Invalid IP build network for scan")
                continue

            count = min(network.num_addresses, 256)
            # network.hosts exclude net dir and broadcast
            for i, ip in enumerate(network.hosts()):
                if i >= count:
                    break
                ip_list.append(str(ip))

        random.shuffle(ip_list)

        return ip_list

    def ping(self, host: str, timeout: float = 0.2) -> dict:
        """
        Realiza un ping a la IP especificada.
        """
        tim_start = time()
        status = {
            'host': host,
            'online': 0,
            'latency': None,
            'error': None,
        }

        try:
            # Crear el socket
            socket_handler = self.create_raw_socket(timeout)
            status["ip"] = socket_handler.resolve_host(host)
            # Construir y enviar el paquete ICMP
            icmp_packet = self.send_icmp_packet(socket_handler, host)

            # Recibir el paquete
            buffer, from_ip = socket_handler.receive_packet(host)
            if buffer is None:
                status['error'] = f"Timeout: No response after {timeout} seconds"
                status['latency'] = -0.001
                return status

            # Procesar el paquete recibido
            status = self.process_received_packet(buffer, host, tim_start)
            return status

        except Exception as e:
            self.logger.error(f"Ping error: {e}")
            status['error'] = str(e)
            return status
        finally:
            socket_handler.close_socket()


    def check_tcp_port(self, host: str, port: int, timeout: float = 1.0) -> dict:
        """Comprueba si un puerto TCP está abierto utilizando SocketHandler."""
        tim_start = time()
        status = {"host": host, "port": port, "online": 0, "protocol": 1, "error": None}
        socket_handler = SocketHandler(timeout)
        try:
            if not socket_handler.create_tcp_socket():
                raise Exception("Failed to create TCP socket")
            if not socket_handler.tcp_connect(host, port):
                status["error"] = f"Failed to connect to {host}:{port}"
            else:
                status["online"] = 1
        except ConnectionError as e:
            self.logger.debug(str(e))
            status["debug"] = str(e)
        except RuntimeError as e:
            self.logger.debug(str(e))
            status["error"] = str(e)
        except Exception as e:
            self.logger.error(str(e))
            status["error"] = str(e)
        finally:
            socket_handler.close()

        status['latency'] = self.calculate_latency(tim_start)

        return status

    def check_udp_port(self, host: str, port: int, timeout: float = 1.0) -> dict:
        """Comprueba si un puerto UDP está abierto utilizando SocketHandler."""
        tim_start = time()
        status = {"host": host, "port": port, "online": 0, "protocol": 2, "error": None}
        socket_handler = SocketHandler(timeout)
        try:
            if not socket_handler.create_udp_socket():
                raise Exception("Failed to create UDP socket")
            if not socket_handler.send(b"ping", (host, port)):
                status["error"] = f"Failed to send data to {host}:{port}"
            else:
                data, address = socket_handler.receive()
                if data:
                    status["online"] = 1
                else:
                    status["error"] = "No response received"
        except ConnectionError as e:
            self.logger.debug(str(e))
            status["error"] = str(e)
        except RuntimeError as e:
            self.logger.error(str(e))
            status["error"] = str(e)
        except Exception as e:
            self.logger.error(str(e))
            status["error"] = str(e)
        finally:
            socket_handler.close()

        status['latency'] = self.calculate_latency(tim_start)

        return status

    def check_http(self, host: str, port: int = 80, timeout: float = 5.0) -> dict:
        """Comprueba si un servidor HTTP responde correctamente."""
        tim_start = time()
        status = {"host": host, "port": port, "online": 0, "protocol": 5, "error": None}
        url = f"http://{host}:{port}"
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                status["online"] = 1
            else:
                status["error"] = f"HTTP error: {response.status_code}"
        except requests.RequestException as e:
            status["error"] = str(e)
        except Exception as e:
            self.logger.error(f"Unexpected error while checking HTTP for {url}: {e}")
            status["error"] = str(e)

        status['latency'] = self.calculate_latency(tim_start)

        return status

    def check_https(self, host: str, port: int = 443, timeout: float = 5.0, verify_ssl = False) -> dict:
        """Comprueba si un servidor HTTPS responde correctamente."""
        tim_start = time()
        status = {"host": host, "port": port, "online": 0, "protocol": 4, "error": None}
        if verify_ssl:
            status['protocol'] = 3

        url = f"https://{host}:{port}"
        try:
            if not verify_ssl:
                urllib3.disable_warnings(InsecureRequestWarning)
            response = requests.get(url, timeout=timeout, verify=verify_ssl)
            if response.status_code == 200:
                status["online"] = 1
            else:
                status["error"] = f"HTTPS error: {response.status_code}"
        except requests.exceptions.SSLError as ssl_error:
            self.logger.error(f"SSL error while checking HTTPS for {url}: {ssl_error}")
            status["error"] = f"SSL error: {ssl_error}"
        except requests.RequestException as e:
            status["error"] = str(e)
        except Exception as e:
            self.logger.error(f"Unexpected error while checking HTTPS for {url}: {e}")
            status["error"] = str(e)
        status['latency'] = self.calculate_latency(tim_start)

        return status

    def process_received_packet(self, buffer: bytes, ip: str, start_time: float) -> dict:
        """Procesa el paquete recibido y devuelve el estado."""
        status = {
            'ip': ip,
            'online': 0,
            'latency': None,
            'error': None,
            'source_ip': None,
            'icmp_type': None,
            'icmp_code': None,
        }

        if len(buffer) < 28:  # Encabezado IP (20 bytes) + Encabezado ICMP (8 bytes)
            self.logger.error("Received packet too short")
            status['error'] = "Packet too short"
            return status

        ip_header = buffer[:20]
        icmp_header = buffer[20:28]
        source_ip = ".".join(map(str, ip_header[12:16]))
        icmp_type, icmp_code = icmp_header[0], icmp_header[1]

        status['source_ip'] = source_ip
        status['icmp_type'] = icmp_type
        status['icmp_code'] = icmp_code

        # 0 ICMP Echo Reply, 8 when this host ping himself
        if source_ip == ip and (icmp_type == 0 or icmp_type == 8):
            status['online'] = 1
            status['latency'] = self.calculate_latency(start_time)
        elif icmp_type == 3:  # ICMP Destination Unreachable
            status['error'] = "Destination Unreachable"
            status['latency'] = -0.001
        else:
            self.logger.warning(f"Unexpected packet: {icmp_type} from {source_ip}, expected: {ip}")
            status['error'] = "Unexpected packet"

        return status

    def create_raw_socket(self, timeout: float) -> SocketRawHandler:
        """Crea y devuelve un socket RAW configurado para ICMP."""
        socket_handler = SocketRawHandler(self.ctx, timeout)
        if not socket_handler.create_socket():
            raise Exception("Socket creation failed")
        return socket_handler

    def send_icmp_packet(self, socket_handler: SocketRawHandler, ip: str) -> bytes:
        """Construye y envía un paquete ICMP."""
        icmp_packet = ICMPPacket().build_packet()
        if not socket_handler.send_packet(ip, icmp_packet):
            raise Exception(f"Failed to send ICMP packet to {ip}")
        return icmp_packet

    def verify_ping_response(self, status: dict, icmp: bytes, start_time: float) -> dict:
        """Verifica la respuesta ICMP y calcula la latencia si es válida."""

        if len(icmp) < 8:
            self.logger.error("ICMP packet too short")
            return status

        icmp_type = icmp[0]
        icmp_code = icmp[1]
        # Type 8 is returned when host pings itself
        if (icmp_type == 0 or icmp_type == 8) and icmp_code == 0:
            if self.verify_checksum(icmp):
                status['online'] = 1
                return status
            self.logger.error(f"Response checksum verification failed")

        return status

    def calculate_latency(self, start_time: float) -> float:
        """Calcula la latencia en milisegundos."""
        return round((time() - start_time) * 1000, 3)

    def verify_checksum(self, icmp: bytes) -> bool:
        """Verifica el checksum de una respuesta ICMP."""
        # Check if len is multiple of 2
        if len(icmp) % 2 != 0:
            self.logger.error("ICMP packet has odd length")
            return False
        try:
            total = 0
            for i in range(0, len(icmp), 2):
                total += struct.unpack('!H', icmp[i:i+2])[0]
            total = (total >> 16) + (total & 0xFFFF)
            return (total + (total >> 16)) == 0xFFFF
        except struct.error:
            self.logger.error("ICMP packet corrupted")
            return False

    @staticmethod
    def is_valid_network(network_str: str) -> bool:
        try:
            ipaddress.IPv4Network(network_str, strict=True)
            return True
        except ValueError:
            return False
