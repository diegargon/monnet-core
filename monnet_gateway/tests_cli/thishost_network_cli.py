import socket
import fcntl
import struct
import os

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

# Main usage
iface = get_default_interface()
if iface:
    ip, netmask = get_ip_and_netmask(iface)
    print(f"Interface: {iface}")
    print(f"IP: {ip}")
    print(f"Netmask: {netmask}")
else:
    print("No default interface found")
