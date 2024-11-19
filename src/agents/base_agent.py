class BaseAgent:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def run(self, input: str) -> str:
        raise NotImplementedError("Subclasses must implement the run method")
