from src.db.prisma import prisma


class ThreadService:
    """
    A service for managing threads.
    """

    @classmethod
    async def find_or_create(cls, id: str):
        existing = await prisma.threads.find_first(
            where={
                "OR": [
                    {"external_id": id},
                    {"id": id},
                ],
            }
        )

        if existing:
            return existing

        return await prisma.threads.create(data={"external_id": id})

    @classmethod
    async def delete(cls, id: str):
        return await prisma.threads.delete_many(
            where={
                "OR": [
                    {"id": id},
                    {"external_id": id},
                ],
            }
        )


thread_service = ThreadService()
