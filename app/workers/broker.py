from taskiq import SmartRetryMiddleware
from taskiq_redis import ListQueueBroker

from app.core.exceptions.exceptions import TransientEmbeddingError
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

retry_middleware = SmartRetryMiddleware(
    default_retry_count=3,
    default_delay=5,
    use_jitter=True,
    use_delay_exponent=True,
    max_delay_exponent=60,
    types_of_exceptions=(TransientEmbeddingError,)
)

broker = broker.with_middlewares(
    retry_middleware
)
