"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""

class AppContext:
    """
    Class AppContext

    Arguments:
        workdir (str): Working directory
    """
    def __init__(self, workdir: str):
        """
        Init
        Args:
            workdir(str): Working Directory
        """
        self.workdir = workdir
        self._database = None
        self._logger = None
        self._config = None
        self._variables = {}

    def set_var(self, key: str, value)-> None:
        """
        Var Setter
        Args:
            key(str):

        """
        self._variables[key] = value

    def get_var(self, key: str):
        """
        Var Getter
        Args:
            key(str):
        """
        return self._variables.get(key, None)

    def has_var(self, key: str) -> bool:
        """
        Check var
        Args:
            key(str)
        Returns:
            bool
        """
        return key in self._variables

    def set_database(self, db_manager) -> None:
        """
        Set database manager
        Args:
            db_manager: Database manager instance
        """
        self._database = db_manager

    def get_database(self):
        """
        Get database manager
        Returns:
            Database manager instance or None
        """
        return self._database

    def has_database(self) -> bool:
        """
        Check if database manager is set
        Returns:
            bool: True if database is set, False otherwise
        """
        return self._database is not None

    def set_config(self, config) -> None:
        """
        Set config
        Args:
            db_manager: Database manager instance
        """
        self._config = config

    def get_config(self):
        """
        Get config
        Returns:
            Config instance or None
        """
        return self._config

    def has_config(self) -> bool:
        """
        Check if config is set
        Returns:
            bool: True if config is set, False otherwise
        """
        return self._config is not None

    def set_logger(self, logger) -> None:
        """
        Set logger
        Args:
            logger: Logger instance
        """
        self._logger = logger

    def get_logger(self):
        """
        Get Logger
        Returns:
            Logger instance
        """
        return self._logger
