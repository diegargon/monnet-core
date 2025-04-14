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
import yaml

# Local
from monnet_gateway.mgateway_config import VERSION, MINOR_VERSION
from shared.app_context import AppContext

def handle_ansible_command(ctx: AppContext, command: str, data_content: dict):
    playbook = data_content.get('playbook', None)
    extra_vars = data_content.get('extra_vars', None)
    ip = data_content.get('ip', None)
    limit = data_content.get('limit', None)
    user = data_content.get('user', "ansible")
    logger = ctx.get_logger()

    if not playbook:
        return {"status": "error", "message": "Playbook not specified"}

    try:
        logger.info("Running ansible playbook...")
        result = run_ansible_playbook(ctx, playbook, extra_vars, ip=ip, user=user, limit=limit)
        result_data = json.loads(result)
        # logpo("ResultData: ", result_data)
        response = {
            "version": str(VERSION) + '.' + str(MINOR_VERSION),
            "status": "success",
            "command": command,
            "result": result_data
        }

        return response
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON: " + str(e))
        return {"status": "error", "message": "Failed to decode JSON: " + str(e)}
    except Exception as e:
        logger.error("Error executing the playbook: " + str(e))
        return {"status": "error", "message": "Error executing the playbook: " + str(e)}

def run_ansible_playbook(ctx: AppContext, playbook: str, extra_vars=None, ip=None, user=None, limit=None):
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
            limit (str): limit

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

    if limit:
        command.extend(['--limit', limit])

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
    Extracts metadata from all YAML playbooks in the directory and stores it in the context.

    Args:
        ctx (AppContext): Context with workdir, logger, and metadata storage capability.

    Returns:
        Optional[List[dict]]: List of metadata dicts if successful, None if critical failure occurs.
                             Also stores the result in ctx via set_pb_metadata().
    """
    # vars
    PLAYBOOKS_DIR = os.path.join(ctx.workdir, 'monnet_gateway', 'playbooks')
    VALID_EXTENSIONS = ('.yml', '.yaml')
    METADATA_REGEX = r'#\s*@meta(.+?)(?=---|\n\s*\n)'
    REQUIRED_FIELDS = {'id', 'name'}


    if not os.path.isdir(PLAYBOOKS_DIR):
        ctx.get_logger().error(f"Playbooks directory not found: {PLAYBOOKS_DIR}")
        return None

    # valid files
    playbook_files = [
        f for f in os.listdir(PLAYBOOKS_DIR)
        if f.lower().endswith(VALID_EXTENSIONS)
        and os.path.isfile(os.path.join(PLAYBOOKS_DIR, f))
    ]

    if not playbook_files:
        ctx.get_logger().warning(f"No valid YAML files found in {PLAYBOOKS_DIR}")
        ctx.set_pb_metadata([])
        return []

    # Scan files
    metadata_list = []
    for filename in playbook_files:
        filepath = os.path.join(PLAYBOOKS_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            if not (metadata_block := re.search(METADATA_REGEX, content, re.DOTALL)):
                ctx.get_logger().debug(f"No metadata found in {filename}")
                continue

            metadata = yaml.safe_load(
                re.sub(r'^\s*#\s*', '', metadata_block.group(1), flags=re.MULTILINE)
            )

            if not metadata or not REQUIRED_FIELDS.issubset(metadata):
                ctx.get_logger().warning(
                    f"Invalid metadata in {filename}. "
                    f"Required fields: {REQUIRED_FIELDS}"
                )
                continue

            metadata['_source_file'] = filename
            metadata_list.append(metadata)

        except yaml.YAMLError as e:
            ctx.get_logger().error(f"YAML syntax error in {filename}: {str(e)}")
        except Exception as e:
            ctx.get_logger().error(f"Unexpected error with {filename}: {str(e)}")

    ctx.set_pb_metadata(metadata_list)

    return metadata_list if metadata_list else None
