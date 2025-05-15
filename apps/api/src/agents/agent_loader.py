import importlib
import inspect
from pathlib import Path

from src.agents.base_agent import BaseAgent
from src.logger import logger

EMPTY_AGENT_CONFIG = {}
EMPTY_HEADERS = {}


class AgentLoader:
    @staticmethod
    def get_agent(
        agent_class: str,
        thread_id: str,
        agent_config: dict = EMPTY_AGENT_CONFIG,
        headers: dict = EMPTY_HEADERS,
    ) -> BaseAgent | None:
        logger.debug(f"Attempting to load agent class: {agent_class}")
        agents_dir = Path(__file__).parent / "implementations"
        logger.debug(f"Scanning directory: {agents_dir}")

        # Get all Python files in the agents directory
        for file in agents_dir.glob("*.py"):
            logger.debug(f"Examining file: {file.name}")
            if file.name == "base_agent.py":
                logger.debug("Skipping base_agent.py")
                continue

            # Import the module
            module_path = f"src.agents.implementations.{file.stem}"
            logger.debug(f"Importing module: {module_path}")
            try:
                module = importlib.import_module(module_path)
            except Exception as e:
                logger.error(f"Failed to import module {module_path}: {e}")
                continue

            # Find all classes in the module that inherit from BaseAgent
            logger.debug(f"Scanning classes in {file.stem}")
            for name, obj in inspect.getmembers(module):
                logger.debug(f"Examining class: {name}")
                if inspect.isclass(obj):
                    logger.debug(f"Class {name} inheritance: {obj.__bases__}")
                    if issubclass(obj, BaseAgent) and obj != BaseAgent and obj.__name__ == agent_class:
                        logger.debug(f"Found matching agent class: {obj}")
                        logger.debug(f"Initializing agent with config: {agent_config}")
                        return obj(thread_id=thread_id, request_headers=headers, **agent_config)

        logger.warning(f"No matching agent found for class: {agent_class}")
        return None

    @staticmethod
    def get_all_agents() -> list[type[BaseAgent]]:
        agents_dir = Path(__file__).parent / "implementations"
        agents = []
        for file in agents_dir.glob("*.py"):
            if file.name == "base_agent.py":
                continue
            module_path = f"src.agents.implementations.{file.stem}"
            module = importlib.import_module(module_path)
            for _, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BaseAgent) and obj != BaseAgent:
                    agents.append(obj)
        return agents
