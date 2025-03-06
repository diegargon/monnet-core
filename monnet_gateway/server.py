"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

Server

"""

# Standard
import json
import socket
import threading

# Local
from monnet_gateway.config import HOST, PORT, PORT_TEST, VERSION, MINOR_VERSION
from monnet_gateway.handlers.handler_client import handle_client
from monnet_gateway.utils.context import AppContext
from shared.logger import log

def run_server(ctx: AppContext):
    """
        Runs Server

        Args:
            ctx (Appcontext): context
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if ctx.has_var('test'):
            port = PORT_TEST
        else:
            port = PORT
        try:
            stop_event = ctx.get_var('stop_event')
            s.settimeout(1.0)
            s.bind((HOST, port))
            s.listen()
            log(f"v{VERSION}.{MINOR_VERSION}: Waiting for connection on {HOST}:{port}...", "info")

            while not stop_event.is_set():
                try:
                    conn, addr = s.accept()
                    threading.Thread(target=handle_client, args=(ctx, conn, addr)).start()
                except socket.timeout:
                    continue
        except Exception as e:
            log(f"Error en el servidor: {str(e)}", "err")
            error_message = {"status": "error", "message": f"Server error: {str(e)}"}
            log(json.dumps(error_message),"debug")
        finally:
            s.close()
