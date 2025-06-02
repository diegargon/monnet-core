"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent - Network Utilities

"""

import re
import subprocess
import time

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

def get_own_mac(interface: str) -> str | None:
    """
    Obtiene la dirección MAC de la interfaz de red especificada.

    Args:
        interface (str): Nombre de la interfaz de red (por ejemplo, 'eth0', 'enp3s0', 'wlan0').

    Returns:
        str | None: La dirección MAC como string si se encuentra, o None.
    """
    try:
        with open(f'/sys/class/net/{interface}/address', 'r') as f:
            mac = f.read().strip()
            if re.fullmatch(r'([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', mac):
                return mac
    except Exception:
        pass
    return None
