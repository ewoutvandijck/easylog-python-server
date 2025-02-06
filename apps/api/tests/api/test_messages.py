import base64

import httpx
import pytest
from fastapi.testclient import TestClient
from src.db.prisma import prisma
from src.main import app
from src.models.messages import ImageContent, TextContent
from src.services.messages.message_service import MessageService

client = TestClient(app)


@pytest.mark.asyncio
async def test_forward_message_calls_agent_implementation():
    prisma.connect()

    thread = prisma.threads.create(
        data={},
    )

    image_url = "https://upload.wikimedia.org/wikipedia/commons/a/a7/Camponotus_flavomarginatus_ant.jpg"
    image_media_type = "image/jpeg"
    image_data = base64.standard_b64encode(httpx.get(image_url).content).decode("utf-8")

    async for chunk in MessageService.forward_message(
        thread_id=thread.id,
        input_content=[
            TextContent(content="Wat staat er in deze afbeelding?"),
            ImageContent(
                content=image_data,
                content_type=image_media_type,
            ),
        ],
        agent_class="AnthropicAssistant",
        agent_config={"debug_interval_ms": 100, "debug_chunk_size": 10},
    ):
        print(chunk)

    prisma.threads.delete(where={"id": thread.id})
    prisma.disconnect()
