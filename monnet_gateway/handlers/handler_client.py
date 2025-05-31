"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

@title: Monnet Gateway - Client Handler
@description: This module handles UI client requests and commands.
"""
import json
import traceback
from time import time

# Local
from monnet_gateway.handlers.handler_ansible import handle_ansible_command
from monnet_gateway.handlers.handler_daemon import handle_daemon_command
from monnet_gateway.handlers.handler_host_command import handle_host_command
from monnet_gateway.mgateway_config import ALLOWED_MODULES
from monnet_shared.app_context import AppContext

def send_response(conn, logger, addr, response):
    """
    Serializa y envía la respuesta al cliente, manejando errores de encoding y conexión.
    """
    try:
        encoded_response = json.dumps(response).encode()
    except (TypeError, ValueError) as encode_error:
        logger.error(f"Failed to encode response: {str(encode_error)}")
        encoded_response = json.dumps(
            {"status": "error", "message": "Internal server error: encoding response"}
        ).encode()
    try:
        conn.sendall(encoded_response)
    except (BrokenPipeError, ConnectionResetError) as conn_error:
        logger.error(f"Failed to send response to {addr}: {str(conn_error)}")
        return False
    except Exception as send_error:
        logger.error(f"Unexpected error while sending response: {str(send_error)}")
        return False
    return True

def handle_client(ctx: AppContext, conn, addr):
    """
        Manage server client

        Args:
            ctx (AppContext): context
            conn: connection object
            addr: address of the client
    """
    logger = ctx.get_logger()

    try:
        logger.info(f"Connection established from {addr}")

        while True:
            data = conn.recv(1024)
            if not data:
                break
            logger.debug(f"Data received: {data}")
            try:
                # Convert received data to JSON
                request = json.loads(data.decode())

                # Check if 'command' exists
                command = request.get('command')
                module = request.get('module')
                if not module:
                    response = {"status": "error", "message": "Module not specified"}
                    send_response(conn, logger, addr, response)
                    break
                if not command:
                    response = {"status": "error", "message": "Command not specified"}
                    send_response(conn, logger, addr, response)
                    break
                if module not in ALLOWED_MODULES:
                    response = {"status": "error", "message": f"Invalid command: {module} {command}"}
                    send_response(conn, logger, addr, response)
                    break

                if module == "ansible":
                    response = handle_ansible_command(ctx, command, request.get('data', {}))
                elif module == "gateway-daemon":
                    response = handle_daemon_command(ctx, command, request.get('data', {}))
                elif module == "host-command":
                    response = handle_host_command(ctx, command, request.get('data', {}))
                # elif module == "another_cmodule":
                #     # Handle 'another_module' logic
                #     pass
                else:
                    response = {"status": "error", "message": f"Invalid module: {module}"}
                logger.debug(f"Response: {response}")
                send_response(conn, logger, addr, response)
                logger.info("Closing client connection")
                break

            except json.JSONDecodeError:
                response = {"status": "error", "message": "Invalid JSON format"}
                send_response(conn, logger, addr, response)
            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                relevant_trace = [frame for frame in tb if "monnet_gateway.py" in frame.filename]
                if relevant_trace:
                    last_trace = relevant_trace[-1]
                else:
                    last_trace = tb[-1]

                error_message = {
                    "status": "error",
                    "message": str(e),
                    "file": last_trace.filename,
                    "line": last_trace.lineno
                }
                conn.sendall(json.dumps(error_message).encode())
                break
        logger.info(f"Connection with {addr} closed")

    except Exception as e:
        logger.error(f"Error handling connection with {addr}: {str(e)}")
    finally:
        conn.close()
