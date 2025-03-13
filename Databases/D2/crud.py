from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

class CRUDBase:
    def __init__(self, model):
        self.model = model

    async def get(self, db: AsyncSession, obj_id: int):
        try:
            result = await db.execute(select(self.model).filter(self.model.id == obj_id))
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"❌ Error getting record: {e}")
            return None

    async def get_all(self, db: AsyncSession, limit: int = 100):
        try:
            result = await db.execute(select(self.model).limit(limit))
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"❌ Error getting all records: {e}")
            return []

    async def create(self, db: AsyncSession, obj_data: dict):
        try:
            obj = self.model(**obj_data)
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"❌ Error creating record: {e}")
            return None

    async def update(self, db: AsyncSession, obj_id: int, update_data: dict):
        try:
            obj = await self.get(db, obj_id)
            if not obj:
                return None
            for key, value in update_data.items():
                setattr(obj, key, value)
            await db.commit()
            await db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"❌ Error updating record: {e}")
            return None

    async def delete(self, db: AsyncSession, obj_id: int):
        try:
            obj = await self.get(db, obj_id)
            if not obj:
                return None
            await db.delete(obj)
            await db.commit()
            return obj
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"❌ Error deleting record: {e}")
            return None
