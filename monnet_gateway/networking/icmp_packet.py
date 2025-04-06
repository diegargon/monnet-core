"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""

import struct
from time import time


import struct
from typing import Optional

class ICMPPacket:
    def __init__(self, identifier: int = 1, sequence: int = 1, payload: bytes = b"ping"):
        self.type = 8  # Echo Request (ICMP)
        self.code = 0
        self.checksum = 0
        self.identifier = identifier
        self.sequence = sequence
        self.payload = payload

    def build_packet(self) -> bytes:
        """Construye el paquete ICMP con checksum."""
        header = struct.pack(
            "!BBHHH",
            self.type,
            self.code,
            self.checksum,  # 0 inicial
            self.identifier,
            self.sequence
        )
        packet = header + self.payload
        self.checksum = self.calculate_checksum(packet)
        # Reempaqueta con el checksum correcto
        header = struct.pack(
            "!BBHHH",
            self.type,
            self.code,
            self.checksum,
            self.identifier,
            self.sequence
        )
        return header + self.payload

    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """Calcula el checksum ICMP (RFC 1071)."""
        if len(data) % 2 != 0:
            data += b"\x00"  # Padding

        sum = 0
        for i in range(0, len(data), 2):
            word = struct.unpack("!H", data[i:i+2])[0]
            sum += word

        sum = (sum >> 16) + (sum & 0xFFFF)
        sum += sum >> 16
        return ~sum & 0xFFFF