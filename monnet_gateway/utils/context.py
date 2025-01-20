"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2024 Diego Garcia (diego/@/envigo.net)

Monnet Ansible Gateway

Class AppContext
"""

class AppContext:
    def __init__(self, workdir: str):
        self.workdir = workdir
        self._database = None
        self._variables = {}

    # Dynamic Vars
    def set_var(self, key: str, value):
        """ Setter """
        self._variables[key] = value

    def get_var(self, key: str):
        """ Getter """
        return self._variables.get(key, None)

    def has_var(self, key: str) -> bool:
        """ Check var """
        return key in self._variables

"""
    @property
    def database(self) -> Database:
        if self._database is None:
            raise ValueError("Database is not initialized.")
        return self._database

    @database.setter
    def database(self, database: Database) -> None:
        self._database = database

    def __repr__(self) -> str:
        return (f"AppContext(workdir={self.workdir}, "
                f"logger={'set' if self._logger else 'not set'}, "
                f"database={'set' if self._database else 'not set'})")
"""