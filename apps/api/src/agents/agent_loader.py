import importlib
import inspect
from pathlib import Path

from src.agents.base_agent import BaseAgent
from src.logger import logger
from src.services.easylog_backend.backend_service import BackendService


class AgentLoader:
    @staticmethod
    def get_agent(
        agent_class: str,
        thread_id: str,
        agent_config: dict = {},
        backend: BackendService | None = None,
    ) -> BaseAgent | None:
        agents_dir = Path("src/agents/implementations")

        # Get all Python files in the agents directory
        for file in agents_dir.glob("*.py"):
            if file.name == "base_agent.py":
                continue

            # Import the module
            module_path = f"src.agents.implementations.{file.stem}"
            module = importlib.import_module(module_path)

            print(file.stem)

            # Find all classes in the module that inherit from BaseAgent
            for _, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseAgent)
                    and obj != BaseAgent
                    and obj.__name__ == agent_class
                ):
                    logger.debug(f"Found agent: {obj}")

                    try:
                        return obj(thread_id=thread_id, backend=backend, **agent_config)
                    except Exception as e:
                        logger.error(f"Error loading agent {obj}: {e}")
                        return None
