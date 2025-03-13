import sys
import os
import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

try:
    from database import SHARDS
    from models import target_metadata
except ImportError:
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.append(parent_dir)
    from database import SHARDS
    from models import target_metadata

config = context.config
fileConfig(config.config_file_name)

async def run_migrations(connection):
    async with connection.begin() as transaction:
        await context.configure(connection=connection, target_metadata=target_metadata)
        await context.run_migrations()

async def run_migrations_online():
    engines = [engine]
    
    for shard_name, shard_url in SHARDS.items():
        engines.append(create_async_engine(shard_url, echo=False))

    for engine in engines:
        async with engine.begin() as connection:
            await run_migrations(connection)

def main():
    asyncio.run(run_migrations_online())

if context.is_offline_mode():
    raise RuntimeError("Migrate just online")
else:
    main()

"""
in cli:
    for create migration file:
        alembic revision --autogenerate -m "Initial migration"
    for migration in all shards and center db:
        alembic upgrade head
"""
