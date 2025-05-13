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
from monnet_gateway.mgateway_config import HOST, PORT, PORT_TEST, GW_F_VERSION
from monnet_gateway.handlers.handler_client import handle_client
from shared.app_context import AppContext

server_socket = None

def run_server(ctx: AppContext):
    """
        Runs Server

        Args:
            ctx (Appcontext): context
    """
    global server_socket

    logger = ctx.get_logger()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if ctx.has_var('test-port'):
        port = PORT_TEST
    else:
        port = PORT
    try:
        stop_event = ctx.get_var('stop_event')
        server_socket.settimeout(1.0)
        server_socket.bind((HOST, port))
        server_socket.listen()
        logger.info(f"v{GW_F_VERSION}: Waiting for connection on {HOST}:{port}...")

        while not stop_event.is_set():
            try:
                conn, addr = server_socket.accept()
                threading.Thread(target=handle_client, args=(ctx, conn, addr)).start()
            except socket.timeout:
                continue
            except OSError as e:
                if stop_event.is_set():
                    break  # Exit loop if the server is stopping
                raise e
    except Exception as e:
        logger.error(f"Error in the server: {str(e)}")
        if not stop_event.is_set():
            stop_event.set()
        # Attempt to respond to the client if a connection exists
        try:
            if 'conn' in locals() and conn:
                error_message = {"status": "error", "message": f"Server error: {str(e)}"}
                conn.sendall(json.dumps(error_message).encode('utf-8'))
                conn.close()
        except Exception as send_error:
            logger.warning(f"Failed to send error response to client: {str(send_error)}")
    finally:
        if server_socket:
            server_socket.close()
            server_socket = None

def stop_server():
    """
    Stops the server by closing the socket
    """
    global server_socket
    if server_socket:
        try:
            server_socket.close()
        except OSError as e:
            pass  # Ignore errors if the socket is already closed
        finally:
            server_socket = None
