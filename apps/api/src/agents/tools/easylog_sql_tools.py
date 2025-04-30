from collections.abc import Callable

from src.agents.tools.base_tools import BaseTools
from src.services.easylog.easylog_sql_service import EasylogSqlService


class EasylogSqlTools(BaseTools):
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
        self.db = EasylogSqlService(
            ssh_key_path=ssh_key_path,
            ssh_host=ssh_host,
            ssh_username=ssh_username,
            db_host=db_host,
            db_port=db_port,
            db_user=db_user,
            db_name=db_name,
            db_password=db_password,
            connect_timeout=connect_timeout,
        ).db

    @property
    def all_tools(self) -> list[Callable]:
        return [self.tool_execute_query]

    async def tool_execute_query(self, query: str) -> str:
        if not self.db:
            raise ValueError("Database not connected")

        with self.db.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()
