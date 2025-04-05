"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""
# Std
import ipaddress
import struct
from time import time, sleep

# Local
from monnet_gateway.database import networks_model
from monnet_gateway.database.hosts_model import HostsModel
from monnet_gateway.handlers.socket_handler import SocketHandler
from monnet_gateway.ping.icmp_packet import ICMPPacket
from shared.app_context import AppContext

class NetworkScanner:
    def __init__(self, ctx: AppContext, networks_model: networks_model.NetworksModel):
        self.ctx = ctx
        self.networks_model = networks_model
        self.logger = self.ctx.get_logger()

    def get_discovery_ips(self, host_model: HostsModel) -> list[str]:
        """
        Get the list of IPs to be scanned
        :return: list of IPs
        """
        ip_list = self.build_ip_list()
        logger = self.ctx.get_logger()

        if not ip_list:
            logger.error("No IPs to scan")
            return []

        all_known_hosts = host_model.get_all() or []

        host_ips = {host['ip'] for host in all_known_hosts}
        ip_list = [ip for ip in ip_list if ip not in host_ips]

        return ip_list

    def build_ip_list(self) -> list[str]:
        ip_list = []
        networks = self.networks_model.get_all()

        if not networks:
            self.logger.notice("No networks found to scan")
            return ip_list

        for net in networks:
            if net.get('disable') or net.get('scan') != 1:
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

    def ping(self, ip: str, timeout: dict = {'sec': 0, 'usec': 50000}) -> dict:
        """Realiza un ping a la IP especificada."""
        status = {'online': 0, 'latency': None}

        # Timeout validation
        if not isinstance(timeout.get('sec'), int) or not isinstance(timeout.get('usec'), int):
            timeout = {'sec': 0, 'usec': 150000}

        tim_start = time()

        # Socket Creation
        socket_handler = SocketHandler(self.ctx, timeout['sec'], timeout['usec'])
        if not socket_handler.create_socket():
            status['error'] = 'socket_create'
            status['latency'] = -0.003
            self.logger.error(f"Pinging error socket creating: {ip}")
            return status

        # Construir el paquete ICMP
        icmp_packet = ICMPPacket()
        packet = icmp_packet.build_packet()

        # Enviar el paquete
        # self.logger.debug(f"Sending packet to {ip} with size {len(packet)} bytes")
        try:
            if not socket_handler.send_packet(ip, packet):
                status['error'] = 'socket_sendto'
                status['latency'] = -0.002
                self.logger.error(f"Pinging error socket connect: {ip}")
                socket_handler.close_socket()
                return status
            buffer, from_ip = socket_handler.receive_packet()
        finally:
            socket_handler.close_socket()

        if buffer is None:
            error_msg = "No packet received (timeout or network issue)"
            self.logger.error(f"{error_msg} from {ip}")
            status['error'] = 'timeout'
            status['latency'] = -0.001
            return status

        # self.logger.debug(f"Received packet from {from_ip} with size {len(buffer)} bytes")
        ip_header = buffer[:20]
        icmp_packet = buffer[20:]
        # self.logger.debug(f"IP header: {ip_header.hex()}")
        # self.logger.debug(f"ICMP packet: {icmp_packet.hex()}")

        # Extraer la dirección IP de origen del encabezado IP
        source_ip = ".".join(map(str, ip_header[12:16]))
        #self.logger.debug(f"Source IP in reply packet: {source_ip}")

        if source_ip == ip:
            return self.verify_ping_response(icmp_packet, ip, tim_start)
        elif icmp_packet[0] != 3:
            # Discard Log Destination Unreachable ip is expected always different
            self.logger.warning(f"Unexpected source IP in reply packet: {icmp_packet[0]} {source_ip}, expected: {ip}")

        status['error'] = 'timeout'
        status['latency'] = -0.001
        socket_handler.close_socket()
        sleep(0.1)

        return status


    def verify_ping_response(self, icmp: bytes, expected_ip: str, start_time: float) -> dict:
        """Verifica la respuesta ICMP y calcula la latencia si es válida."""
        status = {'online': 0, 'latency': None}

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
