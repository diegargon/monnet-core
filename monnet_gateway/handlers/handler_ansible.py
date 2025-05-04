"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Ansible Handler
@description: This module handles server commands related to Ansible playbooks and metadata.

Ansible

"""
# Standard
import json

# Third-party
import yaml

# Local
from monnet_gateway.mgateway_config import GW_F_VERSION
from monnet_gateway.services.ansible_service import AnsibleService
from shared.app_context import AppContext

def handle_ansible_command(ctx: AppContext, command: str, data_content: dict):
    """
        Handle ansible command

        Args:
            ctx (AppContext): context
            command (str): command
            data_content (dict): data content

        Returns:
            dict: response
    """
    ALLOWED_COMMANDS = [
        "playbook_exec",
        "scan_playbooks",
        "get_playbook_metadata",
        "get_all_playbooks_metadata",
        "get_all_pb_meta_ids",
    ]
    if command not in ALLOWED_COMMANDS:
        return {"status": "error", "message": f"Invalid command: {command}"}

    ansible_service = AnsibleService(ctx)

    if command == "playbook_exec":
        return ansible_exec(ctx, ansible_service, command, data_content)
    elif command == "scan_playbooks":
        try:
            ansible_service.extract_pb_metadata()
        except FileNotFoundError as e:
            return _response_error(command, f"Playbooks directory not found: {str(e)}")
        except yaml.YAMLError as e:
            return _response_error(command, f"YAML syntax error: {str(e)}")
        except ValueError as e:
            return _response_error(command, f"Value error: {str(e)}")
        except RuntimeError as e:
            return _response_error(command, f"Runtime error: {str(e)}")
        except Exception as e:
            return _response_error(command, f"Error scanning playbooks: {str(e)}")

        return _response_success(command, "Playbooks scanned successfully")

    elif command == "get_playbook_metadata":
        pid = data_content.get('pid')
        if not pid:
            return {"status": "error", "message": "Playbook ID not specified"}
        try:
            pb_metadata = ansible_service.get_pb_metadata(pid)
        except KeyError as e:
            return _response_error(command, f"Playbook ID not found: {str(e)}")
        except ValueError as e:
            return _response_error(command, str(e))
        except Exception as e:
            return _response_error(command, f"Error retrieving playbook metadata: {str(e)}")

        return _response_success(command, pb_metadata)

    elif command == "get_all_playbooks_metadata":
        try:
            pb_metadata = ansible_service.get_all_pb_metadata()
        except ValueError as e:
            return _response_error(command, str(e))
        except Exception as e:
            return _response_error(command, f"Error retrieving all playbooks metadata: {str(e)}")

        return _response_success(command, pb_metadata)

    elif command == "get_all_pb_meta_ids":
        try:
            pb_metadata = ansible_service.get_all_pb_metadata()
            ids = [meta.get('id') for meta in pb_metadata]
        except ValueError as e:
            return _response_error(command, str(e))
        except Exception as e:
            return _response_error(command, f"Error retrieving all playbook metadata IDs: {str(e)}")

        return _response_success(command, ids)

    return {"status": "error", "message": f"Invalid command: {command}"}

def ansible_exec(ctx: AppContext, ansible_service: AnsibleService, command: str, data_content: dict):
    """
        Execute ansible playbook
        Args:
            ctx (AppContext): context
            command (str): command
            data_content (dict): data content
            Returns:
                dict: response
    """
    playbook = data_content.get('playbook', None)
    extra_vars = data_content.get('extra_vars', None)
    ip = data_content.get('ip', None)
    ansible_group = data_content.get('ansible_group', None)
    user = data_content.get('user', "ansible")
    logger = ctx.get_logger()

    logger.debug(f"Executing ansible playbook... {data_content}")

    if not playbook:
        return _response_error(command, "Playbook not specified")

    # Fetch Ansible variables associated with the hid
    hid = data_content.get('host_id', None)
    if not hid:
        return _response_error(command, "Host ID not specified")

    try:
        ansible_vars = ansible_service.fetch_ansible_vars_by_hid(hid)
        fetched_extra_vars = {var["vkey"]: var["vvalue"] for var in ansible_vars}
    except KeyError as e:
        return _response_error(command, f"Invalid ansible variable format: {str(e)}")
    except Exception as e:
        return _response_error(command, f"Error fetching ansible variables: {str(e)}")

    # Merge fetched extra_vars with existing extra_vars
    if extra_vars:
        fetched_extra_vars.update(extra_vars)
    extra_vars = fetched_extra_vars

    try:
        logger.info("Running ansible playbook... " + str(playbook))
        result = ansible_service.run_ansible_playbook(
            playbook, extra_vars, ip=ip, user=user, ansible_group=ansible_group
        )
        result_data = json.loads(result)
        report_data = _save_report(ctx, data_content, result_data, rtype=1)
        ansible_service.save_report(report_data)

        return _response_success(command, result_data)
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON: " + str(e))
        return _response_error(command, "Failed to decode JSON: " + str(e))
    except Exception as e:
        logger.error("Error executing the playbook: " + str(e))
        return _response_error(command, "Error executing the playbook: " + str(e))

def _response_success(command: str, data:dict):
    """
    Create a success response
    Args:
        command (str): command
        data (dict): data
    Returns:
        dict: response
    """
    response = {
        "version": str(GW_F_VERSION),
        "status": "success",
        "command": command,
        "result": data
    }

    return response

def _response_error(command: str, message: str):
    """
    Create an error response
    Args:
        command (str): command
        message (str): message
        Returns:
            dict: response
    """
    response = {
        "version": str(GW_F_VERSION),
        "status": "error",
        "command": command,
        "message": message,
        "error_msg": message
    }

    return response

def _save_report(self, data: dict, result: dict, rtype: int) -> dict:
    """
    Save the report in the database
    Args:
        task (dict): task
        result (dict): result
        rtype (int): report type
    """
    report_data = {
        "host_id": data["host_id"],
        "pid": data["pid"],
        "source_id": data["source_id"],
        "rtype": rtype,
        "report": json.dumps(result)
    }

    return report_data