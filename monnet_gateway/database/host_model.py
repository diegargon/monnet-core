"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet

"""

from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway.utils.context import AppContext


class HostModel:
    """DB Operations to manage hosts """

    def __init__(self, ctx: AppContext):
        if ctx.has_database():
            self.db = ctx.get_database()
        else:
            if(ctx.get_config()):
                self.db = DBManager(ctx.get_config())
                ctx.set_database(self.db)
            else:
                raise RuntimeError("Database config is not available")

    def get_all(self) -> list[dict]:
        """ List all hosts """
        return self.db.execute_query("SELECT * FROM hosts")
