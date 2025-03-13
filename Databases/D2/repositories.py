from sqlalchemy.ext.asyncio import AsyncSession
from models import User

class AsyncUserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, user_id: str):
        return await self.session.get(User, user_id)

    async def add_user(self, user: User):
        self.session.add(user)
        await self.session.commit()
