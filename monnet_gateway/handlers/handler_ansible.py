"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

@title Monnet Gateway - Ansible Handler
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
        return _response_error(command, f"Command not allowed: {command}")

    if not isinstance(data_content, dict):
        return _response_error(command, f"Invalid data content format: {type(data_content)} {data_content}")

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
            return _response_error(command, "Playbook ID not specified")
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

    return _response_error(command, f"Invalid command: {command}")

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
    playbook_id = data_content.get('pid', None)
    extra_vars = data_content.get('extra_vars', {})
    ip = data_content.get('ip', None)
    ansible_group = data_content.get('ansible_group', None)
    user = data_content.get('user', "ansible")
    logger = ctx.get_logger()

    logger.debug(f"Executing ansible playbook... {data_content}")

    if not playbook_id:
        return _response_error(command, "Playbook not specified")

    # Fetch Ansible variables associated with the hid
    hid = data_content.get('hid', None)
    if not hid:
        return _response_error(command, "Host ID not specified")

    try:
        playbook_vars = ansible_service.fetch_playbook_vars_by_hid(hid)
        fetched_extra_vars = {var["vkey"]: var["vvalue"] for var in playbook_vars}
    except KeyError as e:
        return _response_error(command, f"Invalid ansible variable format: {str(e)}")
    except Exception as e:
        return _response_error(command, f"Error fetching ansible variables: {str(e)}")

    # Merge fetched extra_vars with existing extra_vars
    if isinstance(extra_vars, dict):
        fetched_extra_vars.update(extra_vars)
    extra_vars = fetched_extra_vars

    try:
        logger.info("Running ansible playbook... " + str(playbook_id))
        result = ansible_service.run_ansible_playbook(
            playbook_id, extra_vars, ip=ip, user=user, ansible_group=ansible_group
        )
        try:
            result_data = json.loads(result)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON result for playbook {playbook_id}: {e}")
            return _response_error(command, f"Failed to decode JSON result: {e}. Result: {result}")

        report_data = ansible_service.prepare_report(ctx, data_content, result_data, rtype=1)
        ansible_service.save_report(report_data)

        return _response_success(command, result_data)
    except Exception as e:
        logger.error(f"Error executing the playbook {playbook_id}: {e}")
        return _response_error(command, f"Error executing the playbook: {e}")

def _response_success(command: str, data: dict):
    """
    Create a success response
    Args:
        command (str): command
        data (dict): data
    Returns:
        dict: response
    """
    try:
        response = {
            "version": str(GW_F_VERSION),
            "status": "success",
            "command": command,
            "message": data
        }
        return response
    except (TypeError, ValueError) as e:
        return {
            "version": str(GW_F_VERSION),
            "status": "error",
            "command": command,
            "message": f"Failed to create success response: {e}"
        }

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
        "message": message
    }

    return response