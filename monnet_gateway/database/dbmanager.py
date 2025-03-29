
"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

# Example usage
if __name__ == "__main__":
    config = DBConfig(host="localhost", user="usuario", password="password", database="monnet", driver="mysql-connector")

    try:
        with DBManager(config) as db:
            # Fetch all users
            users = db.fetchall("SELECT * FROM users")
            print(users)

            # Insert a new user within a transaction
            with db.transaction():
                rows_affected = db.execute("INSERT INTO users (username, password) VALUES (%s, %s)", ("John Doe", "test"))
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
            if self.config['python_driver'] == "mysql-connector":
                self._connect_mysql_connector()
            elif self.config['python_driver'] == "pymysql":
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
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database']
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
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database']
            )
            # Return results as dictionaries
            self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        except ImportError:
            raise RuntimeError("PyMySQL is not installed. Install it with `pip install pymysql`.")
        except pymysql.Error as e:
            raise RuntimeError(f"PyMySQL connection failed: {e}")

    @contextmanager
    def transaction(self):
        """Context manager for handling transactions."""
        try:
            yield
            self.commit()
        except Exception as e:
            self.rollback()
            raise RuntimeError(f"Transaction failed: {e}")

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
            raise RuntimeError(f"Query execution failed: {e}")

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
            raise RuntimeError(f"Query execution failed: {e}")

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
            raise RuntimeError(f"Query execution failed: {e}")

    def commit(self):
        """Commit the current transaction."""
        self.conn.commit()

    def rollback(self):
        """Rollback the current transaction."""
        self.conn.rollback()

    def close(self):
        """Close the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
