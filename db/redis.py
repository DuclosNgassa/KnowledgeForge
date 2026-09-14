import redis.asyncio as aioredis

from config import Config

JTI_EXPIRY = 3600

token_block_list = aioredis.StrictRedis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=Config.REDIS_DB,
    password=Config.REDIS_PASSWORD,
)


async def add_jti_to_block_list(jti: str) -> None:
    await token_block_list.set(name=jti, value="", ex=JTI_EXPIRY)


async def token_in_block_list(jti: str) -> bool:
    jti = await  token_block_list.get(name=jti)
    return jti is not None
