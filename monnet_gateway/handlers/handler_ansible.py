"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2024 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

Ansible

"""

import json
import os
import subprocess


def run_ansible_playbook(ctx, playbook, extra_vars=None, ip=None, user=None, limit=None):
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
                f"Error ejecutando ansible playbook: STDOUT: {stdout.decode()} STDERR: {stderr.decode()}"
            )


        return stdout.decode()

    except Exception as e:
        error_message = {
            "status": "error",
            "message": str(e)
        }
        return json.dumps(error_message)