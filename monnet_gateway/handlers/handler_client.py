"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2024 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

Client Handle

"""

import json
import traceback
from monnet_gateway.handlers.handler_ansible import run_ansible_playbook
from shared.log_linux import log, logpo
from config import HOST, PORT, PORT_TEST, VERSION, MINOR_VERSION, ALLOWED_COMMANDS


def handle_client(ctx, conn, addr):
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
                    conn.sendall(json.dumps(response).encode())
                    continue

                # Validate the command
                if command not in ALLOWED_COMMANDS:
                    response = {"status": "error", "message": f"Invalid command: {command}"}
                    conn.sendall(json.dumps(response).encode())
                    continue

                # Extract 'data' content
                data_content = request.get('data', {})

                # Process command-specific logic
                if command == "playbook":
                    # Extract fields specific to the "playbook" command
                    playbook = data_content.get('playbook')
                    extra_vars = data_content.get('extra_vars', {})
                    ip = data_content.get('ip', None)
                    limit = data_content.get('limit', None)
                    user = data_content.get('user', "ansible")

                    # Ensure playbook is specified
                    if not playbook:
                        response = {"status": "error", "message": "Playbook not specified"}
                    else:
                        try:
                            # Execute the playbook and retrieve the result
                            result = run_ansible_playbook(
                                ctx,
                                playbook, extra_vars,
                                ip=ip,
                                user=user,
                                limit=limit
                            )

                            # Convert the result JSON to a dictionary
                            result_data = json.loads(result)  # Expected valid JSON
                            logpo("ResultData: ", result_data)
                            response = {
                                "version": str(VERSION) + '.' + str(MINOR_VERSION),
                                "status": "success",
                                "command": command,
                                "result": {}
                            }
                            response.update(result_data)
                        except json.JSONDecodeError as e:
                            response = {
                                "status": "error",
                                "message": "Failed to decode JSON: " + str(e)
                            }
                        except Exception as e:
                            response = {
                                "status": "error",
                                "message": "Error executing the playbook: " + str(e)
                            }

                # elif command == "another_command":
                #     # Handle 'another_command' logic
                #     pass

                logpo("Response: ", response)
                # Send the response back to the client in JSON format
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

        log(f"Connection with {addr} closed", "info")
        conn.close()

    except Exception as e:
        log(f"Error handling connection with {addr}: {str(e)}", "err")
