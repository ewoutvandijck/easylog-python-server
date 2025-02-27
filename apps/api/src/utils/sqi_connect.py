# Standard library imports
import logging
import os

import pymysql

# Third-party imports
from dotenv import load_dotenv
from pymysql.connections import Connection
from sshtunnel import SSHTunnelForwarder

# Laad alle variabelen uit .env
load_dotenv()


def create_db_connection() -> tuple[SSHTunnelForwarder | None, Connection | None]:
    # Configureer logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    ssh_tunnel = None
    connection = None

    try:
        # Controleer DB_PASSWORD vooraf
        db_password = os.getenv("DB_PASSWORD")
        if not db_password:
            raise ValueError("DB_PASSWORD is niet ingesteld in .env")

        # Pad naar je ED25519 private key
        ssh_key_path = os.path.expanduser("~/.ssh/id_ed25519")
        if not os.path.exists(ssh_key_path):
            raise FileNotFoundError(f"SSH key niet gevonden op pad: {ssh_key_path}")

        logger.info("Start maken SSH tunnel verbinding...")
        ssh_tunnel = SSHTunnelForwarder(
            "staging.easylog.nu",
            ssh_username="forge",
            ssh_pkey=ssh_key_path,
            remote_bind_address=("127.0.0.1", 3306),
        )

        # Start de SSH tunnel
        ssh_tunnel.start()
        logger.info(f"SSH tunnel succesvol gestart op lokale poort: {ssh_tunnel.local_bind_port}")

        # Database verbinding via de tunnel
        logger.info("Maken database verbinding...")
        connection = pymysql.connect(
            host="127.0.0.1",
            port=ssh_tunnel.local_bind_port,
            user="easylog",
            password=db_password,
            database="easylog",
            connect_timeout=10,  # Timeout toevoegen
        )
        logger.info("Database verbinding succesvol tot stand gebracht")

        return ssh_tunnel, connection

    except Exception as e:
        logger.error(f"Fout bij verbinden: {str(e)}")
        # Opruimen bij fouten
        if connection:
            connection.close()
        if ssh_tunnel and ssh_tunnel.is_active:
            ssh_tunnel.close()
        return None, None


if __name__ == "__main__":
    # Test de connectie
    ssh_tunnel, connection = create_db_connection()

    if connection and ssh_tunnel:
        print("\n✅ Database connectie succesvol!\n")

        # Sluit de connecties
        connection.close()
        ssh_tunnel.close()
    else:
        print("\n❌ Database connectie mislukt!\n")
