from src.agents.agent_loader import AgentLoader
from src.lib.prisma import prisma
from src.lib.scheduler import scheduler
from src.logger import logger
from src.models.message_create import MessageCreateInputContent
from src.services.messages.message_service import MessageService


class SuperAgentService:
    @staticmethod
    async def register_super_agents() -> None:
        for agent in AgentLoader.get_all_agents():
            config = agent.super_agent_config()

            if config is None:
                continue

            scheduler.add_job(
                func=SuperAgentService.run_super_agent_job,
                trigger="interval",
                seconds=config.interval_seconds,
                args=[agent.__name__, config.agent_config.model_dump(), config.message_input, config.headers, 15],
            )

            logger.info(f"Registered super agent {agent.__name__} with interval {config.interval_seconds}")

    @staticmethod
    async def run_super_agent_job(
        agent_class: str,
        agent_config: dict,
        message_input: list[MessageCreateInputContent],
        headers: dict,
        max_recursion_depth: int,
    ) -> None:
        threads = await prisma.threads.find_many()

        logger.info(f"Running super agent {agent_class} for {len(threads)} threads")

        for thread in threads:
            agent = AgentLoader.get_agent(agent_class, thread.id, agent_config, headers)

            if agent is None:
                continue

            if not await agent.should_run_super_agent():
                continue

            logger.info(f"Running super agent {agent_class} for thread {thread.id}")

            async for chunk in MessageService.forward_message(
                thread.id,
                message_input,
                agent_class,
                agent_config,
                headers,
                max_recursion_depth,
            ):
                logger.info(f"Chunk: {chunk}")
