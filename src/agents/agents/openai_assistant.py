from typing import Generator

from openai import OpenAI
from openai.types.beta.threads import MessageDeltaEvent, TextDeltaBlock
from typing_extensions import override

from src.agents.base_agent import AgentConfig, BaseAgent
from src.logging import logger
from src.models.messages import MessageContent


class OpenAIAssistantConfig(AgentConfig):
    assistant_id: str


class OpenAIAssistant(BaseAgent):
    client: OpenAI

    def __init__(self):
        self.client = OpenAI(
            api_key="sk-svcacct-URp2x1KVCIDYyYwiqoOuTCe7I2R_RgJ04lyaISPedQep0IK8U2DV4lAT2Vh4J4ATMT3BlbkFJxNo8JF8KQViwfS_POlx8OenLuwlFVRr3LsXGqL5w4-sJDXOj-eS2rY4R4YTLeNWIgA"
        )

    @override
    def on_message(
        self, input: str, config: OpenAIAssistantConfig
    ) -> Generator[MessageContent, None, None]:
        logger.info(
            f"Running OpenAI Assistant with input: {input} and config: {config.model_dump_json()}"
        )

        assistant = self.client.beta.assistants.retrieve(config.assistant_id)

        thread = self.client.beta.threads.create(
            messages=[{"role": "user", "content": input}]
        )

        for x in self.client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=assistant.id, stream=True
        ):
            if isinstance(x.data, MessageDeltaEvent):
                for delta in x.data.delta.content or []:
                    if isinstance(delta, TextDeltaBlock) and delta.text:
                        yield MessageContent(
                            content=delta.text.value or "", type="text"
                        )
