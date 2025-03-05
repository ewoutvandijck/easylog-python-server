import os

import pymysql
from sshtunnel import SSHTunnelForwarder

from src.logger import logger


class EasylogSqlService:
    _instance = None

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

        self.ssh_tunnel = None
        self.connection = None
        self._setup_db_connection()
        self._initialized = True

    def _setup_db_connection(self) -> None:
        """
        Sets up the database connection via SSH tunnel
        """
        try:
            logger.info("Starting database connection setup")
            self.ssh_tunnel, self.connection = self._create_db_connection()

            if self.connection:
                logger.info("Database connection successfully established")
            else:
                logger.error("Could not establish database connection")
        except Exception as e:
            logger.error(f"Error setting up database connection: {str(e)}")

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

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Closes the database connection and SSH tunnel on exit
        """
        if self.connection:
            self.connection.close()
        if self.ssh_tunnel and self.ssh_tunnel.is_active:
            self.ssh_tunnel.close()

    @property
    def db(self) -> pymysql.Connection | None:
        """
        Public access to the database connection
        """
        return self.connection
