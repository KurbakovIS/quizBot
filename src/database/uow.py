from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import SessionLocal


class UnitOfWork:
    def __init__(self):
        self.session: AsyncSession = SessionLocal()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
