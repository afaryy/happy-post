from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.posts import CreatePost
from app.repositories.posts import InMemoryPostRepository


def test_create_post_trims_message() -> None:
    assert CreatePost(message="  hello  ").message == "hello"


def test_create_post_rejects_blank_message() -> None:
    with pytest.raises(ValidationError):
        CreatePost(message="   ")


def test_repository_lists_newest_post_first() -> None:
    timestamps = iter(
        [
            datetime(2026, 7, 31, 10, 0, tzinfo=UTC),
            datetime(2026, 7, 31, 10, 0, tzinfo=UTC) + timedelta(seconds=1),
        ]
    )
    repository = InMemoryPostRepository(clock=lambda: next(timestamps))

    first = repository.create("first")
    second = repository.create("second")

    assert repository.list() == [second, first]


def test_repository_returns_none_for_unknown_id() -> None:
    assert InMemoryPostRepository().get(uuid4()) is None
