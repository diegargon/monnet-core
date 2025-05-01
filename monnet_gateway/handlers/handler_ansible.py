"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

Ansible

"""
# Standard
import json
import os
import re
import subprocess
from typing import List, Optional

# Third-party
import yaml

# Local
from monnet_gateway.mgateway_config import GW_F_VERSION
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
    ALLOWED_COMMANDS = ["playbook_exec", "scan_plabooks", "get_playbooks_metadata"]
    if command not in ALLOWED_COMMANDS:
        return {"status": "error", "message": f"Invalid command: {command}"}

    if command == "playbook_exec":
        return ansible_exec(ctx, command, data_content)
    elif command == "scan_playbooks":
        extract_pb_metadata(ctx)
        return _response_success(command, "Playbooks scanned successfully")
    elif command == "get_playbook_metadata":
        pb_id = data_content.get('pb_id')
        if not pb_id:
            return {"status": "error", "message": "Playbook ID not specified"}
        return get_pb_metadata(ctx, pb_id)

    return {"status": "error", "message": f"Invalid command: {command}"}

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
        "message": message
    }

    return response

def ansible_exec(ctx: AppContext, command: str, data_content: dict):
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

    if not playbook:
        return _response_error(command, "Playbook not specified")

    try:
        logger.info("Running ansible playbook...")
        result = run_ansible_playbook(
            ctx, playbook, extra_vars, ip=ip, user=user, ansible_group=ansible_group
        )
        result_data = json.loads(result)
        # logpo("ResultData: ", result_data)
        return _response_success(command, result_data)
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON: " + str(e))
        return _response_error(command, "Failed to decode JSON: " + str(e))
    except Exception as e:
        logger.error("Error executing the playbook: " + str(e))
        return _response_error(command, "Error executing the playbook: " + str(e))

def run_ansible_playbook(ctx: AppContext, playbook: str, extra_vars=None, ip=None, user=None, ansible_group=None):
    """
        Run Ansible Playbook

        Flags:
            --extra_vars -i ip --limit pattern -u user
        Args:
            ctx (AppContext): context
            playbook (str): playbook
            extra_vars (dict): extra variables
            ip (str): IP address
            user (str): user
            ansible_group (str): group

        Returns:
            str: json response data or "status": error, "message": message
    """
    # extra vars to json
    workdir = ctx.workdir

    extra_vars_str = ""

    if extra_vars:
        extra_vars_str = json.dumps(extra_vars)

    playbook_directory = os.path.join(workdir, 'monnet_gateway/playbooks')
    playbook_path = os.path.join(playbook_directory, playbook)

    command = ['ansible-playbook', playbook_path]

    if extra_vars_str:
        command.extend(['--extra-vars', extra_vars_str])

    if ip:
        command.insert(1, '-i')
        command.insert(2, f"{ip},")

    if ansible_group:
        command.extend(['--limit', ansible_group])

    if user:
        command.extend(['-u', user])

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if stderr:
            raise Exception(
                # TODO to standard json error msg
                f"Error ejecutando ansible playbook: STDOUT: {stdout.decode()} STDERR: {stderr.decode()}"
            )

        return stdout.decode()

    except Exception as e:
        error_message = {
            "status": "error",
            "message": str(e)
        }
        return json.dumps(error_message)

def extract_pb_metadata(ctx: AppContext) -> Optional[List[dict]]:
    """
    Extracts metadata from all YAML playbooks in the directory.
    Handles vars in list format with indentation:
      vars:
        - name: db_username
          type: str
          default: "root"
    """
    PLAYBOOKS_DIR = os.path.join(ctx.workdir, 'monnet_gateway', 'playbooks')
    VALID_EXTENSIONS = ('.yml', '.yaml')
    REQUIRED_FIELDS = {'id', 'name'}
    METADATA_REGEX = r'#\s*@meta\s*(.+?)(?=\n---|\n\s*\n)'

    if not os.path.isdir(PLAYBOOKS_DIR):
        ctx.get_logger().error(f"Playbooks directory not found: {PLAYBOOKS_DIR}")
        return None

    playbook_files = [
        f for f in os.listdir(PLAYBOOKS_DIR)
        if f.lower().endswith(VALID_EXTENSIONS)
        and os.path.isfile(os.path.join(PLAYBOOKS_DIR, f))
    ]

    if not playbook_files:
        ctx.get_logger().warning(f"No valid YAML files found in {PLAYBOOKS_DIR}")
        ctx.set_pb_metadata([])
        return []

    metadata_list = []
    for filename in playbook_files:
        filepath = os.path.join(PLAYBOOKS_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            if not (metadata_block := re.search(METADATA_REGEX, content, re.DOTALL)):
                ctx.get_logger().debug(f"No metadata found in {filename}")
                continue

            # Limpieza de comentarios preservando indentación
            cleaned_lines = []
            for line in metadata_block.group(1).split('\n'):
                if line.strip().startswith('#'):
                    cleaned_line = line.replace('#', '', 1).rstrip()  # Elimina solo el primer #
                    if cleaned_line.strip():  # Ignora líneas vacías
                        cleaned_lines.append(cleaned_line)

            metadata = yaml.safe_load('\n'.join(cleaned_lines))

            if not metadata or not REQUIRED_FIELDS.issubset(metadata):
                ctx.get_logger().warning(f"Invalid metadata in {filename}. Required fields: {REQUIRED_FIELDS}")
                continue

            metadata['_source_file'] = filename
            # ctx.get_logger().debug(f"Metadata extracted from {filename}:\n{json.dumps(metadata, indent=4)}")
            metadata_list.append(metadata)

        except yaml.YAMLError as e:
            ctx.get_logger().error(f"YAML syntax error in {filename}: {str(e)}")
        except Exception as e:
            ctx.get_logger().error(f"Unexpected error with {filename}: {str(e)}")

    ctx.set_pb_metadata(metadata_list)
    return metadata_list if metadata_list else None

def get_pb_metadata(ctx: AppContext, pb_id: str) -> Optional[dict]:
    """
    Retrieve metadata for a specific playbook ID from the context.

    Args:
        ctx (AppContext): Context with metadata storage capability.
        pb_id (str): Playbook ID to search for.

    Returns:
        Optional[dict]: Metadata dict or __response_error if not found.
    """
    if not ctx.has_pb_metadata():
        extract_pb_metadata(ctx)

    pb_metadata = ctx.get_pb_metadata()
    if not pb_metadata:
        return _response_error("get_playbook_metadata", "No metadata found")

    for metadata in pb_metadata:
        if metadata.get('id') == pb_id:
            return _response_success("get_playbook_metadata", metadata)

    return _response_error("get_playbook_metadata", f"Playbook ID {pb_id} not found")
