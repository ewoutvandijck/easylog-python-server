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

    # Pad naar je ED25519 private key
    ssh_key_path = os.path.expanduser("~/.ssh/id_ed25519")

    logger.info("Start maken SSH tunnel verbinding...")

    # SSH Tunnel configuratie met ED25519 key
    ssh_tunnel = SSHTunnelForwarder(
        "staging.easylog.nu",
        ssh_username="forge",
        ssh_pkey=ssh_key_path,
        remote_bind_address=("127.0.0.1", 3306),
    )

    try:
        # Start de SSH tunnel
        ssh_tunnel.start()
        logger.info(f"SSH tunnel succesvol gestart op lokale poort: {ssh_tunnel.local_bind_port}")

        # Haal DB-password uit de omgevingsvariabelen
        db_password = os.getenv("DB_PASSWORD")
        if not db_password:
            raise ValueError("DB_PASSWORD is niet ingesteld in .env")

        # Database verbinding via de tunnel
        logger.info("Maken database verbinding...")
        connection = pymysql.connect(
            host="127.0.0.1",
            port=ssh_tunnel.local_bind_port,
            user="easylog",
            password=db_password,
            database="easylog",
        )
        logger.info("Database verbinding succesvol tot stand gebracht")

        return ssh_tunnel, connection

    except Exception as e:
        logger.error(f"Fout bij verbinden: {str(e)}")
        if ssh_tunnel:
            logger.info("Sluiten SSH tunnel na fout")
            ssh_tunnel.close()
        return None, None


def get_database_tables(connection: Connection) -> list[str]:
    """
    Haalt een lijst op van alle tabellen in de database.

    Args:
        connection: De actieve database connectie

    Returns:
        Een lijst met alle tabelnamen
    """
    try:
        with connection.cursor() as cursor:
            # Query om alle tabellen op te halen
            cursor.execute("SHOW TABLES")
            # Haal alle resultaten op en maak er een lijst van
            tables = [table[0] for table in cursor.fetchall()]
            return tables
    except Exception as e:
        logging.error(f"Fout bij ophalen tabellen: {str(e)}")
        return []


if __name__ == "__main__":
    # Test de connectie
    ssh_tunnel, connection = create_db_connection()

    if connection and ssh_tunnel:
        print("\n✅ Database connectie succesvol!\n")

        # Haal tabellen op en toon ze
        tables = get_database_tables(connection)
        print("Database tabellen:")
        for table in tables:
            print(f"- {table}")

        # Sluit de connecties
        connection.close()
        ssh_tunnel.close()
    else:
        print("\n❌ Database connectie mislukt!\n")
