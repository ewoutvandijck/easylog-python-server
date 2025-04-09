from openai import AsyncStream

from src.agents.implementations.debug_agent import DebugAgent
from src.logger import logger


async def test_messages():
    agent = DebugAgent(thread_id="test")

    response = await agent.on_message(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Call the text tool with a long story"},
                ],
            }
        ]
    )

    if isinstance(response, AsyncStream):
        async for chunk in response:
            logger.info(chunk.choices[0].delta)
    else:
        logger.info(response)

    assert response is not None
