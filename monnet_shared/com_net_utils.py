"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Shared - Network Utilities

"""
import re
import socket
import binascii

def get_default_interface() -> str | None:
    """
    Obtiene el nombre de la interfaz de red principal (default) de la máquina.

    Returns:
        str | None: El nombre de la interfaz (por ejemplo, 'eth0', 'enp3s0') o None si no se puede determinar.
    """
    try:
        # Usa 'ip route' para obtener la interfaz de la ruta por defecto
        output = subprocess.check_output(['ip', 'route', 'show', 'default'], encoding='utf-8')
        # Ejemplo de salida: "default via 192.168.1.1 dev eth0 proto dhcp metric 100"
        for line in output.splitlines():
            parts = line.split()
            if 'dev' in parts:
                idx = parts.index('dev')
                if idx + 1 < len(parts):
                    return parts[idx + 1]
    except Exception:
        pass
    return None

def send_wol(host_mac: str) -> bool:
    """
    Send a Wake-on-LAN (WOL) magic packet to the given MAC address.

    Args:
        host_mac (str): MAC address in format '00:11:22:33:44:55' or '00-11-22-33-44-55'.

    Returns:
        bool: True if the packet was sent successfully.

    Raises:
        ValueError: If the MAC address is invalid.
        RuntimeError: If sending the packet fails.
    """
    mac_clean = host_mac.replace(':', '').replace('-', '')
    if len(mac_clean) != 12 or not re.fullmatch(r'[0-9a-fA-F]{12}', mac_clean):
        raise ValueError(f"MAC address must be 12 hex digits: \"{host_mac}\"")

    try:
        mac_bytes = binascii.unhexlify(mac_clean)
    except binascii.Error:
        raise ValueError(f"MAC address is not correct: \"{host_mac}\"")

    magic_packet = b'\xff' * 6 + mac_bytes * 16

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sent = sock.sendto(magic_packet, ('255.255.255.255', 9))
        sock.close()
    except Exception as e:
        raise RuntimeError(f"Failed sending WOL packet to {host_mac}: {e}")

    if sent == len(magic_packet):
        return True
    else:
        raise RuntimeError(f"Failed sending WOL packet to {host_mac}")
