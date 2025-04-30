import base64

import httpx
import pytest
from fastapi.testclient import TestClient

from src.lib.prisma import prisma
from src.main import app
from src.models.message_create import MessageCreateInputTextContent
from src.services.messages.message_service import MessageService

client = TestClient(app)


@pytest.mark.asyncio
async def test_anthropic_supports_image_data():
    await prisma.connect()

    thread = await prisma.threads.upsert(
        where={"external_id": "test"},
        data={
            "create": {
                "external_id": "test",
            },
            "update": {},
        },
    )

    image_url = "https://upload.wikimedia.org/wikipedia/commons/a/a7/Camponotus_flavomarginatus_ant.jpg"
    image_data = base64.standard_b64encode(httpx.get(image_url).content).decode("utf-8")

    url = f"data:image/jpeg;base64,{image_data}"

    async for chunk in MessageService.forward_message(
        thread_id=thread.id,
        input_content=[
            MessageCreateInputTextContent(text="Welke tools zijn er?"),
        ],
        agent_class="DebugAgent",
        agent_config={
            "prompt": "You can use the following roles: {available_roles}. You are currently using the role: {current_role}. Your prompt is: {current_role_prompt}.\nYou can use the following recurring tasks: {recurring_tasks}. You can use the following reminders: {reminders}. The current time is: {current_time}.\nACT AS AN INTELLIGENT MULTITASKING AGENT \u2014 QUICKLY UNDERSTAND YOUR ROLE, FOLLOW THE GIVEN PROMPT, AND PRIORITIZE ACTIONS BASED ON TIME, TASK RELEVANCE, AND USER CONTEXT.",
            "roles": [
                {
                    "name": "Debugger",
                    "prompt": "[no additional instructions]",
                    "model": "openai/gpt-4.1",
                    "tools_regex": ".*_task|.*_reminder",
                }
            ],
        },
        headers={},
    ):
        print(chunk.model_dump_json(indent=2))
