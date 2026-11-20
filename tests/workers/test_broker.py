from unittest.mock import patch

import pytest

from app.workers import broker as broker_module


@pytest.mark.parametrize(
    ("password", "expected"),
    [
        (
                None,
                "redis://localhost:6379/0",
        ),
        (
                "",
                "redis://localhost:6379/0",
        ),
        (
                "secret",
                "redis://:secret@localhost:6379/0",
        ),
    ],
)
def test_build_redis_url(password, expected):
    with patch.object(
            broker_module.settings,
            "redis_host",
            "localhost",
    ), patch.object(
        broker_module.settings,
        "redis_port",
        6379,
    ), patch.object(
        broker_module.settings,
        "redis_db",
        0,
    ), patch.object(
        broker_module.settings,
        "redis_password",
        password,
    ):
        assert broker_module.build_redis_url() == expected


def test_broker_is_configured():
    assert broker_module.broker is not None


def test_retry_middleware_is_configured():
    assert broker_module.retry_middleware is not None
