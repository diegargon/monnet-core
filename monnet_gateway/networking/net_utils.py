"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Net utils

"""
import re
import socket
import subprocess
import ipaddress
import csv

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


def _format_mac_vendor(mac: str) -> str | None:
    # Remove any non-alphanumeric characters
    cleaned_mac = re.sub(r'[^a-fA-F0-9]', '', mac)

    # Ensure the MAC has at least 6 characters
    if len(cleaned_mac) < 6:
        return None

    formatted_mac = cleaned_mac[:6]

    return formatted_mac

def get_org_from_mac(mac: str) -> str | None:
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

def get_hostname(ip: str) -> str | None:
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
