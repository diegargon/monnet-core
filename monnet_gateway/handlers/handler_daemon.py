"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

@title Monnet Gateway - Gateway Daemon Handler
@description: This module handles commands related to the Monnet Gateway daemon
"""
from monnet_gateway.services.ansible_service import AnsibleService
from time import time


def handle_daemon_command(ctx, command, data):
    """
    Handle system-level commands like restart, shutdown, etc.

    Args:
        ctx (AppContext): Application context.
        command (str): Command name.
        data (dict): Additional data for the command.

    Returns:
        dict: Response dictionary.
    """
    logger = ctx.get_logger()

    if command == "restart-daemon":
        logger.notice("Restart command received. Restarting daemon...")
        # This would work only if systemd is used and set to restart always
        ctx.get_var('stop_event').set()
        return {"status": "success", "message": "Daemon is restarting"}
    elif command == "reload-pbmeta":
        logger.notice("Reloading Playbook metadata...")
        ansibleService = AnsibleService(ctx)
        try:
            ansibleService.extract_pb_metadata()
        except FileNotFoundError as e:
            return {"status": "error", "message": f"Playbooks directory not found: {str(e)}"}
        except ValueError as e:
            return {"status": "error", "message": f"Value error: {str(e)}"}
        except RuntimeError as e:
            return {"status": "error", "message": f"Runtime error: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Error reloading playbook metadata: {str(e)}"}

        return {"status": "success", "message": "Playbook metadata reloaded"}
    elif command == "reload-config":
        logger.notice("Reloading configuration...")
        config = ctx.get_config()
        config.reload()
        return {"status": "success", "message": "Configuration reloaded"}
    elif command == "ping":
        logger.debug("Ping command received.")
        client_timestamp = data.get("timestamp")
        if client_timestamp is None:
            return {"status": "error", "message": "Missing timestamp in ping request"}

        try:
            server_timestamp = time()
            latency_ms = (server_timestamp - float(client_timestamp)) * 1000
            return {
                "status": "success",
                "message": "pong",
                "latency_ms": round(latency_ms, 3),
                "server_timestamp": server_timestamp
            }
        except ValueError:
            return {"status": "error", "message": "Invalid timestamp format"}
    else:
        return {"status": "error", "message": f"Unknown gatteway-daemon command: {command}"}
