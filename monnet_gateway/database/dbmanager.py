"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - DBManager

# Example usage
if __name__ == "__main__":
    config = DBConfig(
        host="localhost",
        user="usuario",
        password="password",
        database="monnet",
        driver="mysql-connector"
    )

    try:
        with DBManager(config) as db:
            # Fetch all users
            users = db.fetchall("SELECT * FROM users")
            print(users)

            # Insert a new user within a transaction
            with db.transaction():
                rows_affected = db.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)", ("John Doe", "test")
                )
                print(f"Rows inserted: {rows_affected}")
    except RuntimeError as e:
        print(e)

"""

from typing import List, Tuple, Union, Optional, Dict
from contextlib import contextmanager
import importlib

class DBManager:
    """
    MySQL database wrapper with optional dependencies and improved error handling.
    """

    def __init__(self, config: dict):
        """
        Initialize the database connection.

        :param config: Database configuration.
        """
        self.config = config
        self.conn = None
        self.cursor = None
        self._connect()

    def _connect(self):
        """Establish the database connection based on the selected driver."""


        try:
            if self.config.get('python_driver') == "mysql-connector":
                self._connect_mysql_connector()
            elif self.config.get('python_driver') == "pymysql":
                self._connect_pymysql()
            else:
                raise ValueError("Unsupported driver. Use 'mysql-connector' or 'pymysql'.")
        except Exception as e:
            raise RuntimeError(f"Database connection failed: {e}")

    def _connect_mysql_connector(self):
        """Connect using mysql-connector-python."""
        try:
            mysql_connector = importlib.import_module("mysql.connector")
            self.conn = mysql_connector.connect(
                host=self.config.get('host'),
                port=self.config.get('port'),
                user=self.config.get('user'),
                password=self.config.get('password'),
                database=self.config.get('database')
            )
            # Return results as dictionaries
            self.cursor = self.conn.cursor(dictionary=True)
        except ImportError:
            raise RuntimeError("mysql-connector-python is not installed. \
                Install it with `pip install mysql-connector-python`.")
        except mysql_connector.Error as e:
            raise RuntimeError(f"mysql-connector connection failed: {e}")

    def _connect_pymysql(self):
        """Connect using PyMySQL."""
        try:
            pymysql = importlib.import_module("pymysql")
            self.conn = pymysql.connect(
                host=self.config.get('host'),
                port=self.config.get('port'),
                user=self.config.get('user'),
                password=self.config.get('password'),
                database=self.config.get('database')
            )
            # Return results as dictionaries
            self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        except ImportError:
            raise RuntimeError("PyMySQL is not installed. Install it with `pip install pymysql`.") from e
        except pymysql.Error as e:
            raise RuntimeError(f"PyMySQL connection failed: {e}") from e

    @contextmanager
    def transaction(self):
        """Context manager for handling transactions."""
        try:
            yield
            self.commit()
        except Exception as e:
            self.rollback()
            raise RuntimeError(f"Transaction failed: {e}") from e

    def insert(self, table: str, data: dict) -> int:
        """
        Inserta un registro en la tabla especificada.
        Args:
            table (str): Nombre de la tabla.
            data (dict): Diccionario con los datos a insertar.
        Returns:
            int: ID del registro insertado.
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f"%({key})s" for key in data.keys())
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.execute(query, data)

        return  self.cursor.lastrowid

    def update(self, table: str, data: dict, where: dict) -> int:
        """
        Actualiza un registro en la tabla especificada.
        Args:
            table (str): Nombre de la tabla.
            data (dict): Diccionario con los datos a actualizar.
            where (dict): Condiciones para el `WHERE`.
        """
        set_clause = ", ".join(f"{key} = %({key})s" for key in data.keys())
        where_clause = " AND ".join(f"{key} = %({key})s" for key in where.keys())
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = {**data, **where}

        return self.execute(query, params)

    def execute(self, query: str, params: Union[Tuple, List] = None) -> int:
        """
        Execute an INSERT, UPDATE, DELETE query.

        :param query: SQL query to execute.
        :param params: Parameters for the query.
        :return: Number of affected rows.
        """
        try:
            self.cursor.execute(query, params)
            return self.cursor.rowcount
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}") from e

    def fetchone(self, query: str, params: Union[Tuple, List] = None) -> Optional[Dict]:
        """
        Execute a SELECT query and return one row.

        :param query: SQL query to execute.
        :param params: Parameters for the query.
        :return: A single row as a dictionary.
        """
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}") from e

    def fetchall(self, query: str, params: Union[Tuple, List] = None) -> List[Dict]:
        """
        Execute a SELECT query and return all rows.

        :param query: SQL query to execute.
        :param params: Parameters for the query.
        :return: List of all rows as dictionaries.
        """
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}") from e

    def commit(self):
        """Commit the current transaction."""
        self.conn.commit()

    def rollback(self):
        """Rollback the current transaction."""
        self.conn.rollback()

    def close(self):
        """Close the database connection."""
        try:
            if getattr(self, 'cursor', None) is not None:
                self.cursor.close()
        except Exception as e:
            raise RuntimeError(f"Error closing cursor: {e}") from e
        try:
            if getattr(self, 'conn', None) is not None:
                self.conn.close()
        except Exception as e:
            raise RuntimeError(f"Error closing connection: {e}") from e

        self.cursor = None
        self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
