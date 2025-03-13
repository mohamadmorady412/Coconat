import os
import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv("DB_URL", "mysql+asyncmy://user:password@main_host:3306/db")

SHARDS = {
    'shard_1': os.getenv("SHARD_1_URL", "mysql+asyncmy://user:password@shard1:3306/db"),
    'shard_2': os.getenv("SHARD_2_URL", "mysql+asyncmy://user:password@shard2:3306/db")
}

try:
    engine = create_async_engine(
        DATABASE_URL, 
        echo=False, 
        future=True,
        pool_size=10,       
        max_overflow=20
    )
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    logger.info("✅ Database engine and session created successfully.")
except Exception as e:
    logger.error(f"❌ Error creating database engine: {e}")
    raise

shard_engines = defaultdict(lambda: None)
shard_sessions = defaultdict(lambda: None)

for name, url in SHARDS.items():
    try:
        shard_engines[name] = create_async_engine(
            url, 
            echo=False, 
            future=True,
            pool_size=5,
            max_overflow=10     
        )
        shard_sessions[name] = sessionmaker(bind=shard_engines[name], expire_on_commit=False, class_=AsyncSession)
        logger.info(f"✅ Shard {name} engine and session created successfully.")
    except Exception as e:
        logger.error(f"❌ Error creating shard {name} engine: {e}")

@asynccontextmanager
async def get_db():
    """get new session from center-db"""
    session = SessionLocal()
    try:
        yield session
    finally:
        await session.close()

@asynccontextmanager
async def get_shard_session(shard_name: str):
    """get new session form shard"""
    if shard_name not in shard_sessions or shard_sessions[shard_name] is None:
        logger.warning(f"⚠️ Shard {shard_name} not found. Using default database.")
        async with get_db() as session:
            yield session
    else:
        session = shard_sessions[shard_name]()
        try:
            yield session
        finally:
            await session.close()
