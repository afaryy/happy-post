from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from app.domain.posts import Post


class PostRepository(Protocol):
    def create(self, message: str) -> Post: ...

    def list(self) -> list[Post]: ...

    def get(self, post_id: UUID) -> Post | None: ...


class InMemoryPostRepository:
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))
        self._posts: list[Post] = []

    def create(self, message: str) -> Post:
        post = Post(id=uuid4(), message=message, created_at=self._clock())
        self._posts.append(post)
        return post

    def list(self) -> list[Post]:
        return sorted(self._posts, key=lambda post: post.created_at, reverse=True)

    def get(self, post_id: UUID) -> Post | None:
        return next((post for post in self._posts if post.id == post_id), None)
