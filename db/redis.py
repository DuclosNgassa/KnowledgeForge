import redis.asyncio as aioredis

from core.settings import settings

JTI_EXPIRY = 3600

token_block_list = aioredis.StrictRedis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    password=settings.redis_password,
)


async def add_jti_to_block_list(jti: str) -> None:
    await token_block_list.set(name=jti, value="", ex=JTI_EXPIRY)


async def token_in_block_list(jti: str) -> bool:
    jti = await  token_block_list.get(name=jti)
    return jti is not None
