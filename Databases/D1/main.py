import asyncio
import aiosqlite
from alembic import op
import sqlalchemy as sa
from dataclasses import dataclass
from typing import Optional
import logging

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

@dataclass
class User:
    id: Optional[int] = None
    name: str = ''
    age: int = 0

class DatabaseError(Exception):
    pass

class UserRepository:
    def __init__(self, db):
        self.db = db

    async def get_user(self, id: int):
        return await User.get(self.db, id)

    async def save_user(self, user: User):
        async with self.db.cursor() as cursor:
            await cursor.execute("BEGIN")
            try:
                await user.save(cursor)
                await self.db.commit()
            except aiosqlite.Error as e:
                logger.error(f"Error saving user: {e}")
                await self.db.rollback()
                raise DatabaseError(f"Error saving user: {e}")

    async def update_user(self, user: User):
        async with self.db.cursor() as cursor:
            await cursor.execute("BEGIN")
            try:
                await user.update(cursor)
                await self.db.commit()
            except aiosqlite.Error as e:
                logger.error(f"Error updating user: {e}")
                await self.db.rollback()
                raise DatabaseError(f"Error updating user: {e}")

    async def delete_user(self, user: User):
        async with self.db.cursor() as cursor:
            await cursor.execute("BEGIN")
            try:
                await user.delete(cursor)
                await self.db.commit()
            except aiosqlite.Error as e:
                logger.error(f"Error deleting user: {e}")
                await self.db.rollback()
                raise DatabaseError(f"Error deleting user: {e}")

class QueryBuilder:
    def __init__(self, model):
        self.model = model
        self.where_clauses = []
        self.where_values = []
        self.order_by_clause = None
        self.limit_clause = None

    def where(self, **kwargs):
        for key, value in kwargs.items():
            self.where_clauses.append(f'{key} = ?')
            self.where_values.append(value)
        return self

    def order_by(self, field, direction='ASC'):
        self.order_by_clause = f'ORDER BY {field} {direction}'
        return self

    def limit(self, limit):
        self.limit_clause = f'LIMIT {limit}'
        return self

    async def execute(self, db):
        query = f'SELECT * FROM {self.model.__name__.lower()}'
        if self.where_clauses:
            query += ' WHERE ' + ' AND '.join(self.where_clauses)
        if self.order_by_clause:
            query += ' ' + self.order_by_clause
        if self.limit_clause:
            query += ' ' + self.limit_clause
        try:
            async with db.execute(query, tuple(self.where_values)) as cursor:
                rows = await cursor.fetchall()
                return [self.model(**dict(zip(self.model.fields.keys(), row))) for row in rows]
        except aiosqlite.Error as e:
            logger.error(f"Error executing query: {e}")
            raise DatabaseError(f"Error executing query: {e}")        

class Model:
    @classmethod
    async def create_table(cls, db):
        fields = ', '.join([f'{name} {data_type}' for name, data_type in cls.fields.items()])
        try:
            await db.execute(f'CREATE TABLE IF NOT EXISTS {cls.__name__.lower()} ({fields})')
            await db.commit()
        except aiosqlite.Error as e:
            logger.error(f"Error creating table {cls.__name__}: {e}")
            raise DatabaseError(f"Error creating table: {e}")

    @classmethod
    async def get(cls, db, id: int):
        try:
            async with db.execute(f'SELECT * FROM {cls.__name__.lower()} WHERE id = ?', (id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return cls(**dict(zip(cls.fields.keys(), row)))
                return None
        except aiosqlite.Error as e:
            logger.error(f"Error getting record {cls.__name__} with id {id}: {e}")
            raise DatabaseError(f"Error getting record: {e}")

    async def save(self, db):
        fields = ', '.join(self.fields.keys())
        values = ', '.join(['?' for _ in range(len(self.fields))])
        try:
            await db.execute(f'INSERT INTO {self.__class__.__name__.lower()} ({fields}) VALUES ({values})', tuple(self.__dict__.values()))
            await db.commit()
        except aiosqlite.Error as e:
            logger.error(f"Error saving record {self.__class__.__name__}: {e}")
            raise DatabaseError(f"Error saving record: {e}")

    async def update(self, db):
        fields = ', '.join([f'{name} = ?' for name in self.fields.keys() if name != 'id'])
        values = tuple([getattr(self, name) for name in self.fields.keys() if name != 'id']) + (self.id,)
        try:
            await db.execute(f'UPDATE {self.__class__.__name__.lower()} SET {fields} WHERE id = ?', values)
            await db.commit()
        except aiosqlite.Error as e:
            logger.error(f"Error updating record {self.__class__.__name__} with id {self.id}: {e}")
            raise DatabaseError(f"Error updating record: {e}")

    async def delete(self, db):
        try:
            await db.execute(f'DELETE FROM {self.__class__.__name__.lower()} WHERE id = ?', (self.id,))
            await db.commit()
        except aiosqlite.Error as e:
            logger.error(f"Error deleting record {self.__class__.__name__} with id {self.id}: {e}")
            raise DatabaseError(f"Error deleting record: {e}")

def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String),
        sa.Column('age', sa.Integer)
    )

def downgrade():
    op.drop_table('user')

class User(User, Model):
    fields = {'id': 'INTEGER PRIMARY KEY AUTOINCREMENT', 'name': 'TEXT', 'age': 'INTEGER'}

async def example_query_builder(db):
    try:
        users = await QueryBuilder(User).where(age=30).order_by('name').limit(10).execute(db)
        for user in users:
            print(user)
    except DatabaseError as e:
        print(f"QueryBuilder failed: {e}")

async def main(user_repository: UserRepository):
    try:
        await User.create_table(user_repository.db)
        user = User(name='علی', age=30)
        await user_repository.save_user(user)
        retrieved_user = await user_repository.get_user(1)
        if retrieved_user:
            print(retrieved_user.name)
            retrieved_user.age = 31
            await user_repository.update(retrieved_user)
            await user_repository.delete(retrieved_user)
        await example_query_builder(user_repository.db)

    except DatabaseError as e:
        print(f"Database operation failed: {e}")

if __name__ == '__main__':
    async def run_main():
        async with aiosqlite.connect('mydatabase.db') as db:
            user_repository = UserRepository(db)
            await main(user_repository)
    asyncio.run(run_main())