import asyncio
import datetime
import json
import uuid
from collections.abc import Callable

from pydantic import BaseModel

from src.agents.tools.base_tools import BaseTools
from src.lib.graphiti import get_graphiti_connection


class KnowledgeGraphTools(BaseTools):
    def __init__(self, thread_id: str, entities: dict[str, type[BaseModel]] | None = None) -> None:
        self.thread_id = thread_id
        self.entities = entities

    @property
    def all_tools(self) -> list[Callable]:
        return [
            self.tool_store_episode,
            self.tool_search_knowledge_base,
        ]

    async def tool_store_episode(self, conversation_summary: str, episode_body: str) -> None:
        """Store a new episode in the knowledge graph.

        This tool adds a new episode to the knowledge graph, which can be retrieved later
        for context and memory. The episode includes a summary and detailed content.

        Args:
            conversation_summary: A very short summary of the conversation"
            episode_body: The body of the episode.

        Returns:
            The episode that was stored.

        Examples:
            >>> tool_store_episode(
            ...     conversation_summary="Discussion about AI ethics",
            ...     episode_body="User asked about ethical considerations in AI development. Assistant explained the importance of transparency, fairness, and accountability in AI systems.",
            ... )
            '{"id": "episode-123", "name": "thread-abc_1", "source": "message", "source_description": "Discussion about AI ethics", "content": "User asked about ethical considerations...", "valid_at": "2023-01-01T00:00:00Z", "entity_edges": []}'

            >>> tool_store_episode(
            ...     conversation_summary="Python programming help",
            ...     episode_body="User needed help with Python list comprehensions. Assistant provided examples and explained the syntax and use cases.",
            ... )
            '{"id": "episode-456", "name": "thread-xyz_2", "source": "message", "source_description": "Python programming help", "content": "User needed help with Python list comprehensions...", "valid_at": "2023-01-01T00:00:00Z", "entity_edges": []}'
        """
        graphiti_connection = get_graphiti_connection()
        asyncio.create_task(
            graphiti_connection.add_episode(
                name=f"{self.thread_id}_{str(uuid.uuid4())[:8]}",
                episode_body=episode_body,
                source_description=conversation_summary,
                reference_time=datetime.datetime.now(),
                group_id=self.thread_id,
                entity_types=self.entities,  # type: ignore
            )
        )

    async def tool_search_knowledge_base(self, query: str) -> str:
        """
        Search the knowledge base for a query.

        Args:
            query: The query to search the knowledge base with.

        Returns:
            A list of results from the knowledge base.

        Examples:
            >>> tool_search_knowledge_base(query="What is the capital of France?")
            '[{"id": "episode-123", "name": "thread-abc_1", "source": "message", "source_description": "Discussion about AI ethics", "content": "User asked about ethical considerations...", "valid_at": "2023-01-01T00:00:00Z", "entity_edges": []}]'
        """

        results = await get_graphiti_connection().search(query, group_ids=[self.thread_id])

        return json.dumps(
            [
                result.model_dump_json(exclude={"fact_embedding", "valid_at", "invalid_at", "expired_at"})
                for result in results
            ],
        )
