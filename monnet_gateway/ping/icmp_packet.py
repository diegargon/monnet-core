"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""

import struct
from time import time


class ICMPPacket:
    def __init__(self, identifier=b"\x00\x01", sequence=b"\x00\x01", payload=b"ping"):
        self.type = b"\x08"  # Echo Request
        self.code = b"\x00"
        self.checksum = b"\x00\x00"  # Placeholder for checksum
        self.identifier = identifier
        self.sequence = sequence
        self.payload = payload

    def build_packet(self):
        """Construye el paquete ICMP completo con su checksum."""
        package = self.type + self.code + self.checksum + self.identifier + self.sequence + self.payload
        expected_size = len(self.type + self.code + self.checksum + self.identifier + self.sequence) + len(self.payload)
        checksum = self.calculate_checksum(package)
        return self.type + self.code + checksum + self.identifier + self.sequence + self.payload


    def calculate_checksum(self, data: bytes) -> bytes:
        """Calcula el checksum de los paquetes ICMP."""
        sum = 0
        count_to = (len(data) // 2) * 2
        count = 0

        while count < count_to:
            this_val = data[count + 1] * 256 + data[count]
            sum = sum + this_val
            sum = sum & 0xFFFFFFFF  # Keep sum within 32 bits
            count = count + 2

        if count_to < len(data):
            sum = sum + data[len(data) - 1]
            sum = sum & 0xFFFFFFFF

        sum = (sum >> 16) + (sum & 0xFFFF)
        sum = sum + (sum >> 16)
        answer = ~sum & 0xFFFF
        answer = answer >> 8 | (answer << 8 & 0xFF00)
        return struct.pack('H', answer)