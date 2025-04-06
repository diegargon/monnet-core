"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""
# Std
import ipaddress
import struct
from time import time, sleep

# Local
from monnet_gateway.database.hosts_model import HostsModel
from monnet_gateway.database.networks_model import NetworksModel
from monnet_gateway.handlers.socket_handler import SocketHandler
from monnet_gateway.ping.icmp_packet import ICMPPacket
from shared.app_context import AppContext

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

            network_address = network.network_address
            broadcast_address = network.broadcast_address

            count = min(network.num_addresses, 256)
            for i, ip in enumerate(network.hosts()):
                if i >= count:
                    break
                if ip != network_address and ip != broadcast_address:
                    ip_list.append(str(ip))

        return ip_list

    def ping(self, ip: str, timeout: float = 1.2) -> dict:
        """
            Realiza un ping a la IP especificada.
            latency is used with negative values to indicate errors in graphs
        """
        status = {
            'ip': ip,
            'online': 0,
            'latency_ms': None,
            'error_type': None,
            'error_details': None,
            'source_ip': None,
            'from_ip': None,
            'icmp_type': None,
            'icmp_code': None
        }

        tim_start = time()

        try:
            # Socket Creation
            socket_handler = SocketHandler(self.ctx, timeout)
            if not socket_handler.create_socket():
                status['latency'] = -0.003  # F
                raise Exception("Socket creation failed: {ip}")

            # Construir el paquete ICMP
            icmp_packet = ICMPPacket().build_packet()

            # Enviar el paquete
            # self.logger.debug(f"Sending packet to {ip} with size {len(packet)} bytes")

            if not socket_handler.send_packet(ip, icmp_packet):
                status['latency'] = -0.002
                raise Exception("Send_packet failed: {ip}")

            buffer, from_ip = socket_handler.receive_packet()
            status['from_ip'] = from_ip

            if buffer is None:
                error_msg = f'Timeout: No response after {timeout["sec"]}.{timeout["usec"]}s from {ip}'
                status['error'] = error_msg
                status['latency'] = -0.001
                return status

            # self.logger.debug(f"Received packet from {from_ip} with size {len(buffer)} bytes")
            ip_header = buffer[:20]
            icmp_header = buffer[20:28]
            icmp_type, icmp_code = icmp_header[0], icmp_header[1]
            # Extraer la dirección IP de origen del encabezado IP
            source_ip = ".".join(map(str, ip_header[12:16]))
            status['source_ip'] = source_ip
            status['icmp_type'] = icmp_type
            status['icmp_code'] = icmp_code

            if source_ip == ip: # ICMP Echo Reply
                return self.verify_ping_response(status, icmp_packet, ip, tim_start)
            elif icmp_packet[0] == 3:  # ICMP Destination Unreachable
                status['error'] = 'Destination_unreachable'
                status['latency'] = self.calculate_latency(tim_start)
                self.logger.warning(f"Destination unreachable from {source_ip} (code {icmp_packet[1]})")
                return status
            else:
                self.logger.warning(f"Unexpected reply packet: {icmp_packet[0]} {source_ip}, expected: {ip}")

            status['error'] = 'timeout'
            status['latency'] = -0.001

            return status
        except Exception as e:
            self.logger.error(str(e))
            status['error'] = str(e)
            return status

        finally:
            socket_handler.close_socket()

    def verify_ping_response(self, status: dict, icmp: bytes, expected_ip: str, start_time: float) -> dict:
        """Verifica la respuesta ICMP y calcula la latencia si es válida."""

        if len(icmp) < 2:
            self.logger.error("ICMP packet too short")
            return status

        type = icmp[0]
        code = icmp[1]

        # Type 8 is returned when host pings itself
        if (type == 0 or type == 8) and code == 0:
            if self.verify_checksum(icmp):
                status['online'] = 1
                status['latency'] = self.calculate_latency(start_time)
                return status
            else:
                self.logger.error(f"Response checksum verification failed")

        return status

    def calculate_latency(self, start_time: float) -> float:
        """Calcula la latencia en milisegundos."""
        return round((time() - start_time) * 1000, 4)

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
