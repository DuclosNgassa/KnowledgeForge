from taskiq_redis import ListQueueBroker

from app.core.settings import settings


def build_redis_url() -> str:
    password = (
        f":{settings.redis_password}@"
        if settings.redis_password
        else ""
    )

    return (
        f"redis://{password}"
        f"{settings.redis_host}:"
        f"{settings.redis_port}/"
        f"{settings.redis_db}"
    )


broker = ListQueueBroker(
    build_redis_url(),
    max_connection_pool_size=3,
    socket_timeout=None,
    socket_connect_timeout=5,
)
