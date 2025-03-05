import contextlib
import os

import pymysql
from sshtunnel import SSHTunnelForwarder

from src.logger import logger


class EasylogSqlService:
    def __init__(
        self,
        ssh_key_path: str | None = None,
        ssh_host: str | None = None,
        ssh_username: str | None = None,
        db_host: str = "127.0.0.1",
        db_port: int = 3306,
        db_user: str = "easylog",
        db_name: str = "easylog",
        db_password: str = "",
        connect_timeout: int = 10,
    ) -> None:
        self.use_ssh = all([ssh_key_path, ssh_host, ssh_username])
        self.ssh_key_path = os.path.expanduser(ssh_key_path) if ssh_key_path else None
        self.ssh_host = ssh_host
        self.ssh_username = ssh_username
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_name = db_name
        self.db_password = db_password
        self.connect_timeout = connect_timeout

        # We'll create connections on demand
        self.ssh_tunnel = None
        self.connection = None
        logger.info("EasylogSqlService initialized (connections will be created on demand)")

    def _create_db_connection(self) -> tuple[SSHTunnelForwarder | None, pymysql.Connection | None]:
        ssh_tunnel = None
        connection = None

        try:
            if not self.db_password:
                raise ValueError("Password not provided")

            if self.use_ssh:
                if not self.ssh_key_path or not os.path.exists(self.ssh_key_path):
                    raise FileNotFoundError(f"SSH key not found at path: {self.ssh_key_path}")

                logger.info("Establishing SSH tunnel connection...")
                ssh_tunnel = SSHTunnelForwarder(
                    self.ssh_host,
                    ssh_username=self.ssh_username,
                    ssh_pkey=self.ssh_key_path,
                    remote_bind_address=(self.db_host, self.db_port),
                )

                ssh_tunnel.start()
                logger.info(f"SSH tunnel successfully started on local port: {ssh_tunnel.local_bind_port}")
                connection_port = ssh_tunnel.local_bind_port
            else:
                logger.info("Direct database connection without SSH tunnel...")
                connection_port = self.db_port

            logger.info("Establishing database connection...")
            connection = pymysql.connect(
                host=self.db_host,
                port=connection_port,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                connect_timeout=self.connect_timeout,
            )
            logger.info("Database connection successfully established")
            logger.info(
                f"db_host: {self.db_host}, db_port: {connection_port}, db_user: {self.db_user}, db_name: {self.db_name}"
            )

            return ssh_tunnel, connection

        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            if connection:
                connection.close()
            if ssh_tunnel and ssh_tunnel.is_active:
                ssh_tunnel.close()
            return None, None

    @contextlib.contextmanager
    def get_connection(self):
        """
        Context manager that provides a fresh database connection and ensures it's properly closed.

        Usage:
            with sql_service.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM table")
                    results = cursor.fetchall()
        """
        ssh_tunnel, connection = self._create_db_connection()
        try:
            if connection is None:
                raise RuntimeError("Failed to establish database connection")
            yield connection
        finally:
            if connection:
                connection.close()
            if ssh_tunnel and ssh_tunnel.is_active:
                ssh_tunnel.close()
            logger.debug("Database connection and SSH tunnel closed")

    def execute_query(self, query: str, params=None):
        """
        Execute a query with a fresh connection and return results
        """
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params)

                    # Fetch results if it's a SELECT query
                    if query.strip().upper().startswith("SELECT"):
                        return cursor.fetchall()
                    else:
                        connection.commit()
                        return cursor.rowcount
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            return None

    def close(self):
        """
        Explicitly close any open connections
        """
        if self.connection:
            self.connection.close()
            self.connection = None
        if self.ssh_tunnel and self.ssh_tunnel.is_active:
            self.ssh_tunnel.close()
            self.ssh_tunnel = None
        logger.info("Database connections closed")

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Close connections on exit
        """
        self.close()

    @property
    def db(self) -> pymysql.Connection | None:
        """
        Get a connection to the database.
        Note: The caller is responsible for closing this connection.
        """
        if self.connection is None:
            self.ssh_tunnel, self.connection = self._create_db_connection()
        return self.connection
