import base64

import httpx
import pytest
from fastapi.testclient import TestClient
from src.db.prisma import prisma
from src.main import app
from src.models.messages import ImageContent, PDFContent, TextContent
from src.services.messages.message_service import MessageService

client = TestClient(app)


@pytest.mark.asyncio
async def test_anthropic_supports_image_data():
    return
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
        agent_class="DebugAnthropic",
        agent_config={},
    ):
        print(chunk)

    async for chunk in MessageService.forward_message(
        thread_id=thread.id,
        input_content=[
            TextContent(content="Wat stond er ook alweer in deze afbeelding?"),
        ],
        agent_class="DebugAnthropic",
        agent_config={},
    ):
        print(chunk)

    prisma.threads.delete(where={"id": thread.id})
    prisma.disconnect()
    pass


@pytest.mark.asyncio
async def test_anthropic_supports_pdf_data():
    return
    prisma.connect()

    thread = prisma.threads.create(
        data={},
    )

    pdf_url = "https://assets.anthropic.com/m/1cd9d098ac3e6467/original/Claude-3-Model-Card-October-Addendum.pdf"
    pdf_data = base64.standard_b64encode(httpx.get(pdf_url).content).decode("utf-8")

    async for chunk in MessageService.forward_message(
        thread_id=thread.id,
        input_content=[
            PDFContent(
                content=pdf_data,
            ),
        ],
        agent_class="DebugAnthropic",
        agent_config={},
    ):
        print(chunk)

    async for chunk in MessageService.forward_message(
        thread_id=thread.id,
        input_content=[
            TextContent(content="Sla een memory op dat mijn naam Jasper is"),
        ],
        agent_class="DebugAnthropic",
        agent_config={},
    ):
        print(chunk)

    async for chunk in MessageService.forward_message(
        thread_id=thread.id,
        input_content=[
            TextContent(content="Wat is mijn naam?"),
        ],
        agent_class="DebugAnthropic",
        agent_config={},
    ):
        print(chunk)

    image_url = "https://upload.wikimedia.org/wikipedia/commons/a/a7/Camponotus_flavomarginatus_ant.jpg"
    image_media_type = "image/jpeg"
    image_data = base64.standard_b64encode(httpx.get(image_url).content).decode("utf-8")

    async for chunk in MessageService.forward_message(
        thread_id=thread.id,
        input_content=[
            TextContent(
                content="Wat hebben de afbeelding en de pdf met elkaar gemeen?"
            ),
            ImageContent(
                content=image_data,
                content_type=image_media_type,
            ),
        ],
        agent_class="DebugAnthropic",
        agent_config={},
    ):
        print(chunk)

    prisma.threads.delete(where={"id": thread.id})
    prisma.disconnect()


@pytest.mark.asyncio
async def test_anthropic_supports_tool_use():
    prisma.connect()

    thread = prisma.threads.create(
        data={},
    )

    async for chunk in MessageService.forward_message(
        thread_id=thread.id,
        input_content=[
            TextContent(content="Sla een herinnering op dat mijn naam Jasper is"),
        ],
        agent_class="DebugAnthropic",
        agent_config={},
    ):
        print(chunk)

    async for chunk in MessageService.forward_message(
        thread_id=thread.id,
        input_content=[
            TextContent(content="Wat is mijn naam op"),
        ],
        agent_class="DebugAnthropic",
        agent_config={},
    ):
        print(chunk)

    prisma.threads.delete(where={"id": thread.id})
    prisma.disconnect()
