from typing import Generator, List

from src.agents.base_agent import AgentConfig, BaseAgent
from src.models.messages import Message, MessageContent
from anthropic import Anthropic

class AnthropicWithPDFConfig(AgentConfig):
    pass


class AnthropicWithPDF(BaseAgent):
    client: Anthropic

    def __init__(self):
        self.client = Anthropic(
            api_key=self.get_env("ANTHROPIC_API_KEY"),
        )

    def on_message(
        self, messages: List[Message], config: AnthropicWithPDFConfig
    ) -> Generator[MessageContent, None, None]:
        
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0,
            system="You are a world-class poet. Respond only with short poems.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Why is the ocean salty?"
                        }
                    ]
                }
            ]
        )

        yield MessageContent(content=str(response))
