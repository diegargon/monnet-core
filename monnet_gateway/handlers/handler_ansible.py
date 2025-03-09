"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

Ansible

"""
# Standard
import json
import os
import subprocess

# Local
from monnet_gateway.config import VERSION, MINOR_VERSION
from monnet_gateway.utils.context import AppContext
from shared.logger import log

def handle_ansible_command(ctx: AppContext, command: str, data_content: dict):
    playbook = data_content.get('playbook', None)
    extra_vars = data_content.get('extra_vars', None)
    ip = data_content.get('ip', None)
    limit = data_content.get('limit', None)
    user = data_content.get('user', "ansible")

    if not playbook:
        return {"status": "error", "message": "Playbook not specified"}

    try:
        log("Running ansible playbook...", "info")
        result = run_ansible_playbook(ctx, playbook, extra_vars, ip=ip, user=user, limit=limit)
        result_data = json.loads(result)
        # logpo("ResultData: ", result_data)
        response = {
            "version": str(VERSION) + '.' + str(MINOR_VERSION),
            "status": "success",
            "command": command,
            "result": {}
        }
        # TODO  fix result must be in result (need frontend reports fix)
        response.update(result_data)
        return response
    except json.JSONDecodeError as e:
        log("Failed to decode JSON: " + str(e), "err")
        return {"status": "error", "message": "Failed to decode JSON: " + str(e)}
    except Exception as e:
        log("Error executing the playbook: " + str(e), "err")
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
