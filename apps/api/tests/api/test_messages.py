import base64
import os

import dotenv
import httpx
import pytest
import weaviate
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from weaviate.classes.query import MetadataQuery

from src.lib.prisma import prisma
from src.main import app
from src.models.message_create import MessageCreateInputTextContent
from src.services.messages.message_service import MessageService

load_dotenv()

client = TestClient(app)


@pytest.mark.asyncio
async def test_anthropic_supports_image_data():
    await prisma.connect()

    thread = await prisma.threads.upsert(
        where={"external_id": "test2"},
        data={
            "create": {
                "external_id": "test2",
            },
            "update": {},
        },
    )

    image_url = "https://upload.wikimedia.org/wikipedia/commons/a/a7/Camponotus_flavomarginatus_ant.jpg"
    image_data = base64.standard_b64encode(httpx.get(image_url).content).decode("utf-8")

    url = f"data:image/jpeg;base64,{image_data}"

    from src.lib.weaviate import weaviate_client

    async with weaviate_client:
        async for chunk in MessageService.forward_message(
            thread_id=thread.id,
            input_content=[
                MessageCreateInputTextContent(text="Zoek kennis over de M5M6 Metro"),
            ],
            agent_class="DebugAgent",
            agent_config={
                "prompt": "You can use the following roles: {available_roles}. You are currently using the role: {current_role}. Your prompt is: {current_role_prompt}.\nYou can use the following recurring tasks: {recurring_tasks}. You can use the following reminders: {reminders}. The current time is: {current_time}.\nACT AS AN INTELLIGENT MULTITASKING AGENT \u2014 QUICKLY UNDERSTAND YOUR ROLE, FOLLOW THE GIVEN PROMPT, AND PRIORITIZE ACTIONS BASED ON TIME, TASK RELEVANCE, AND USER CONTEXT.",
                "roles": [
                    {
                        "name": "Helpful Assistant",
                        "prompt": "[no additional instructions]",
                        "model": "openai/gpt-4.1",
                        "tools_regex": ".*",
                    }
                ],
            },
            headers={},
        ):
            print(chunk.model_dump_json(indent=2))


@pytest.mark.asyncio
async def test_find_with_weaviate_document():
    dotenv.load_dotenv()
    await prisma.connect()

    async with weaviate.use_async_with_local(
        headers={
            "X-Openai-Api-Key": os.getenv("OPENAI_API_KEY") or "",
        }
    ) as client:
        collection = client.collections.get(name="documents")

        results = await collection.query.hybrid(
            query="What did we agree with ducata on?",
            limit=5,
            alpha=0.5,
            auto_limit=1,
            return_metadata=MetadataQuery.full(),
        )

        print(results)
