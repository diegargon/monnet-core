"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Shared: Context

"""

from shared.clogger import Logger

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
        self._logger = None
        self._config = None
        self._pb_metadata = {}
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

    def set_config(self, config) -> None:
        """
        Set config
        Args:
            Config instance or none
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

    def set_logger(self, logger: Logger) -> None:
        """
        Set logger
        Args:
            logger: Logger instance
        """
        self._logger = logger

    def get_logger(self) -> Logger:
        """
        Get Logger
        Returns:
            Logger instance
        """
        return self._logger

    def set_pb_metadata(self, metadata: dict) -> None:
        """
        Set playbook metadata.
        Args:
            metadata (dict): Metadata dictionary.
        """
        self._pb_metadata = metadata

    def get_pb_metadata(self) -> dict:
        """
        Get playbook metadata.
        Returns:
            dict: Metadata dictionary.
        """
        return self._pb_metadata

    def has_pb_metadata(self) -> bool:
        """
        Check if playbook metadata is set.
        Returns:
            bool: True if metadata is set, False otherwise.
        """
        return bool(self._pb_metadata)
