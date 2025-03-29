"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

"""

import subprocess
from shared.app_context import AppContext
from shared.logger import log

class HostCheckerTask:
    """ Verify known hosts """
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.log = ctx.get_logger()
    #    self.hosts = ctx.get_var("known_hosts", [])

    def run(self):
        log("Verifying known hosts ...", "debug")

    def ping_host(self, host):
        """ Ping check """
        log(f"Ping {host}...", "debug")
