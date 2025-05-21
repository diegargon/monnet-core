"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway CLI TEST

"""

import json
from pathlib import Path
import sys

from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway.tests_cli.common_cli import init_context
from monnet_gateway.handlers.handler_ansible import handle_ansible_command

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

if __name__ == "__main__":
    ctx = init_context("/opt/monnet-core")
    ctx.get_logger().log("Starting test_config CLI", "info")
    pid = input("Enter Playbook ID (leave empty to fetch all metadata): ").strip()

    if pid:
        command = "get_playbook_metadata"
        data_content = {"pid": pid}
    else:
        command = "get_all_playbooks_metadata"
        data_content = {}

    response = handle_ansible_command(ctx, command, data_content)
    print("Response:")
    print(json.dumps(response, indent=4))
