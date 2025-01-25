"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2024 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

Server

"""

import json
import socket
import threading
from config import HOST, PORT, PORT_TEST, VERSION, MINOR_VERSION, ALLOWED_COMMANDS
from monnet_gateway.handlers.handler_client import handle_client
from shared.log_linux import log

def run_server(ctx):
    """
        Runs Server

        Args:
            Appcontext: ctx
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
            log(f"v{VERSION}.{MINOR_VERSION}: Esperando conexión en {HOST}:{port}...", "info")

            while not stop_event.is_set():
                try:
                    conn, addr = s.accept()
                    threading.Thread(target=handle_client, args=(ctx, conn, addr)).start()
                except socket.timeout:
                    continue
        except Exception as e:
            log(f"Error en el servidor: {str(e)}", "err")
            error_message = {"status": "error", "message": f"Error en el servidor: {str(e)}"}
            log(json.dumps(error_message))

