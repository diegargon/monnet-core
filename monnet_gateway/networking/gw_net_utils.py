"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Net utils

"""
import re
import socket
import subprocess
import ipaddress
import csv
import fcntl
import struct



def is_valid_ip(ip):
    """Validate if the given IP is a valid IPv4 address."""
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ValueError:
        return False

def get_mac(ip):
    """Get the MAC address for a given IP address."""
    if not is_valid_ip(ip):
        return None

    try:
        result = subprocess.check_output(['ip', 'neigh', 'show', ip], stderr=subprocess.STDOUT)
        result = result.decode('utf-8')
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None

    # Search for MAC address in the output
    mac = re.search(r'([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}', result)
    if mac:
        return mac.group(0)

    return None


def _format_mac_vendor(mac: str):
    # Remove any non-alphanumeric characters
    cleaned_mac = re.sub(r'[^a-fA-F0-9]', '', mac)

    # Ensure the MAC has at least 6 characters
    if len(cleaned_mac) < 6:
        return None

    formatted_mac = cleaned_mac[:6]

    return formatted_mac

def get_org_from_mac(mac: str):
    """
    Busca la organización asociada a una dirección MAC en el archivo OUI.

    Args:
        mac (str): Dirección MAC a buscar.
        oui_file (str): Ruta al archivo OUI (CSV).

    Returns:
        str | None: Nombre de la organización si se encuentra, de lo contrario None.
    """
    oui_file_path = "/opt/monnet-core/monnet_gateway/files/oui.csv"

    # Formatear la MAC para obtener el vendor
    mac_vendor = _format_mac_vendor(mac)
    if not mac_vendor:
        return None

    try:
        # Abrir el archivo CSV y buscar el vendor
        with open(oui_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["Assignment"].strip().upper() == mac_vendor.upper():
                    return row["Organization Name"].strip()
    except FileNotFoundError:
        return None
    #    print(f"Error: El archivo {oui_file} no existe.")
    except KeyError as e:
        return None
    #    print(f"Error: Falta la columna esperada en el archivo CSV: {e}")
    except Exception as e:
        return None
    #    print(f"Error inesperado: {e}")

    return None

def get_hostname(ip: str):
    """
    Obtiene el hostname asociado a una dirección IP.

    Args:
        ip (str): Dirección IP a buscar.

    Returns:
        str | None: Hostname si se encuentra, de lo contrario None.
    """
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname
    except socket.herror:
        return None
    except Exception as e:
        return None

def same_network(ip1: str, ip2: str, netmask: int = 24) -> bool:
    """
    Devuelve True si ip1 e ip2 están en la misma red /netmask.

    Args:
        ip1 (str): Primera dirección IP.
        ip2 (str): Segunda dirección IP.
        netmask (int): Prefijo de red (por defecto 24).

    Returns:
        bool: True si ambas IPs están en la misma red.
    """
    import ipaddress
    try:
        net1 = ipaddress.IPv4Interface(f"{ip1}/{netmask}").network
        net2 = ipaddress.IPv4Interface(f"{ip2}/{netmask}").network
        return net1 == net2
    except Exception:
        return False

def get_default_interface():
    """Get the default network interface from the routing table"""
    with open('/proc/net/route') as f:
        for line in f.readlines()[1:]:
            fields = line.strip().split()
            iface, dest, flags = fields[0], fields[1], int(fields[3], 16)
            if dest == '00000000' and flags & 2:  # default route and UP
                return iface
    return None

def get_ip_and_netmask(iface):
    """Get IP address and netmask of an interface"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Get IP
    ip = socket.inet_ntoa(fcntl.ioctl(
        sock.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', iface[:15].encode('utf-8'))
    )[20:24])

    # Get Netmask
    netmask = socket.inet_ntoa(fcntl.ioctl(
        sock.fileno(),
        0x891b,  # SIOCGIFNETMASK
        struct.pack('256s', iface[:15].encode('utf-8'))
    )[20:24])

    return ip, netmask