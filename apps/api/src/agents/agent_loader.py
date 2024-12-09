import importlib
import inspect
from pathlib import Path

from src.agents.base_agent import BaseAgent
from src.logger import logger


class AgentLoader:
    agents: list[BaseAgent] = []

    def __init__(self, thread_id: str) -> None:
        self.load_agents(thread_id)

    def get_agent(self, agent_class: str) -> BaseAgent | None:
        return next(
            (agent for agent in self.agents if agent.__class__.__name__ == agent_class),
            None,
        )

    def load_agents(self, thread_id: str):
        agents_dir = Path("src/agents/implementations")

        # Get all Python files in the agents directory
        for file in agents_dir.glob("*.py"):
            if file.name == "base_agent.py":
                continue

            # Import the module
            module_path = f"src.agents.implementations.{file.stem}"
            module = importlib.import_module(module_path)

            # Find all classes in the module that inherit from BaseAgent
            for _, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseAgent)
                    and obj != BaseAgent
                ):
                    logger.debug(f"Found agent: {obj}")

                    try:
                        self.agents.append(obj(thread_id=thread_id))
                    except Exception as e:
                        logger.error(f"Error loading agent {obj}: {e}")
