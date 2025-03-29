"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

"""

from shared.app_context import AppContext
from monnet_gateway.handlers.handler_ansible import run_ansible_playbook

class AnsibleTask:
    """Ejecuta tareas Ansible según la configuración en la base de datos."""
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        #self.db = DBManager()
        #self.ansible_runner = AnsibleRunner()

    def run(self):
        pass
        #log("Execution ansible task...", "debug")
        #tasks = self.db.get_ansible_tasks()
        #for task in tasks:
        #    self.ansible_runner.run_task(task)
