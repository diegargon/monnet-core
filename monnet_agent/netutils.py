import socket
import binascii
import re
import subprocess
import time

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

def get_mac_from_ip(ip: str) -> str | None:
    """
    Get the MAC address associated with an IP address using the system ARP table.

    Args:
        ip (str): The IP address to query.

    Returns:
        str | None: The MAC address as a string if found, else None.
    """
    try:
        # Hacer ping antes de consultar la tabla ARP
        try:
            subprocess.run(['ping', '-c', '1', '-W', '1', ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5)
        except Exception:
            pass
        # Use 'ip neigh' (Linux) or fallback to 'arp -n'
        try:
            output = subprocess.check_output(['ip', 'neigh', 'show', ip], encoding='utf-8')
            # Output example: "192.168.1.10 dev eth0 lladdr 00:11:22:33:44:55 REACHABLE"
            for line in output.splitlines():
                parts = line.split()
                if ip in parts and 'lladdr' in parts:
                    idx = parts.index('lladdr')
                    return parts[idx + 1]
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to arp -n
            output = subprocess.check_output(['arp', '-n', ip], encoding='utf-8')
            # Output example: "192.168.1.10 ether 00:11:22:33:44:55 C eth0"
            for line in output.splitlines():
                if ip in line:
                    parts = line.split()
                    for part in parts:
                        if re.fullmatch(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', part):
                            return part
    except Exception:
        pass
    return None