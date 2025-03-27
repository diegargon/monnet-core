
from database.dbmanager import DBManager
from monnet_gateway.utils.context import AppContext
from shared.logger import log
from monnet_gateway.handlers.handler_ansible import run_ansible_playbook

class AnsibleTask:
    """Ejecuta tareas Ansible según la configuración en la base de datos."""
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        #self.db = DBManager()
        #self.ansible_runner = AnsibleRunner()

    def run(self):
        log("Execution ansible task...", "debug")
        #tasks = self.db.get_ansible_tasks()
        #for task in tasks:
        #    self.ansible_runner.run_task(task)

