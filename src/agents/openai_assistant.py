from src.agents.base_agent import BaseAgent


class OpenAIAssistant(BaseAgent):
    def __init__(self, name: str, description: str):
        super().__init__(name, description)

    def run(self, input: str) -> str:
        return "Hello, world!"
