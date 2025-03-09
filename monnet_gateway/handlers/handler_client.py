"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

Client Handle

"""

import json
import traceback
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Local
from monnet_gateway.handlers.handler_ansible import handle_ansible_command
from monnet_gateway.utils.context import AppContext
from shared.logger import log, logpo
from monnet_gateway.config import ALLOWED_COMMANDS


def handle_client(ctx: AppContext, conn, addr):
    """
        Manage server client

        Args:
            ctx (AppContext): context
            conn: connection object
            addr: address of the client
    """
    try:
        log(f"Connection established from {addr}", "info")

        while True:
            data = conn.recv(1024)
            if not data:
                break
            logpo("Data: ", data)
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
                # elif command == "another_command":
                #     # Handle 'another_command' logic
                #     pass
                else:
                    response = {"status": "error", "message": f"Invalid command: {command}"}
                logpo("Response: ", response)
                # Send the response back to the client in JSON format
                conn.sendall(json.dumps(response).encode())
                log("Closing client connection")
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
        log(f"Connection with {addr} closed", "info")

    except Exception as e:
        log(f"Error handling connection with {addr}: {str(e)}", "err")
    finally:
        conn.close()
