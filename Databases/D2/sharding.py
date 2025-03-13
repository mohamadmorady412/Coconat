from Databases.D2.database import SHARDS
from sqlalchemy.orm import Session

class ShardRouter:
    def get_shard(self, shard_key: str) -> Session:
        hash_value = hash(shard_key)
        shard_id = f'shard_{hash_value % len(SHARDS) + 1}'
        return SHARDS[shard_id]
