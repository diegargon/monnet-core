"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

Client Handle

"""

import json
import traceback

# Local
from monnet_gateway.handlers.handler_ansible import extract_pb_metadata, handle_ansible_command
from monnet_gateway.mgateway_config import ALLOWED_COMMANDS
from shared.app_context import AppContext

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
                if not command:
                    response = {"status": "error", "message": "Command not specified"}
                elif command not in ALLOWED_COMMANDS:
                    # Validate the command
                    response = {"status": "error", "message": f"Invalid command: {command}"}
                elif command == "playbook":
                    response = handle_ansible_command(ctx, command, request.get('data', {}))
                elif command == "scan_playbooks":
                    response == extract_pb_metadata(ctx)
                # elif command == "another_command":
                #     # Handle 'another_command' logic
                #     pass
                else:
                    response = {"status": "error", "message": f"Invalid command: {command}"}
                logger.debug(f"Response: {response}")
                # Send the response back to the client in JSON format
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
                    break
                except Exception as send_error:
                    logger.error(f"Unexpected error while sending response: {str(send_error)}")
                    break
                logger.info("Closing client connection")
                break

            except json.JSONDecodeError:
                response = {"status": "error", "message": "Invalid JSON format"}
                conn.sendall(json.dumps(response).encode())
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
