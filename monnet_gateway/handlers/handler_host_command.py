"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia

@title: Monnet Gateway - Host Power Handler
@description: Encapsula la lógica de los comandos de power (reboot, shutdown, power_on) para hosts.
"""

def handle_host_command(ctx, command, data):
    if not command:
        return {"status": "error", "message": "Command not specified"}
    if not data or "host_id" not in data:
        return {"status": "error", "message": "Missing host_id in data"}

    if command == "power_on":
        pass
    else:
        return {"status": "error", "message": "Unknown power command"}
