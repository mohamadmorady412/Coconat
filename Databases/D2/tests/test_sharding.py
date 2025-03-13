import pytest

from ifpd import ifpd
ifpd()

from models import User
from sharding import ShardRouter

@pytest.mark.asyncio
async def test_shard_distribution():
    user1 = User(shard_key="user_123")
    user2 = User(shard_key="user_456")
    
    router = ShardRouter()
    assert router.get_shard(user1.shard_key) != router.get_shard(user2.shard_key)
