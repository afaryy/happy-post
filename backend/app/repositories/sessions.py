from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from app.db.models import user_sessions_table
from app.security import hash_session_token


class SessionRepository(Protocol):
    def create(self, user_id: UUID, token: str, ttl_seconds: int) -> None: ...

    def get_user_id(self, token: str) -> UUID | None: ...

    def delete(self, token: str) -> None: ...


def utc_now() -> datetime:
    return datetime.now(UTC)


class InMemorySessionRepository:
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or utc_now
        self._sessions: dict[str, tuple[UUID, datetime]] = {}

    def create(self, user_id: UUID, token: str, ttl_seconds: int) -> None:
        self._sessions[hash_session_token(token)] = (
            user_id,
            self._clock() + timedelta(seconds=ttl_seconds),
        )

    def get_user_id(self, token: str) -> UUID | None:
        token_hash = hash_session_token(token)
        session = self._sessions.get(token_hash)
        if session is None:
            return None
        user_id, expires_at = session
        if expires_at <= self._clock():
            self._sessions.pop(token_hash, None)
            return None
        return user_id

    def delete(self, token: str) -> None:
        self._sessions.pop(hash_session_token(token), None)


class SqlAlchemySessionRepository:
    def __init__(self, engine: Engine, clock: Callable[[], datetime] | None = None) -> None:
        self._engine = engine
        self._clock = clock or utc_now

    def create(self, user_id: UUID, token: str, ttl_seconds: int) -> None:
        now = self._clock()
        with self._engine.begin() as connection:
            connection.execute(
                user_sessions_table.insert().values(
                    id=uuid4(),
                    user_id=user_id,
                    session_token_hash=hash_session_token(token),
                    expires_at=now + timedelta(seconds=ttl_seconds),
                    created_at=now,
                )
            )

    def get_user_id(self, token: str) -> UUID | None:
        token_hash = hash_session_token(token)
        now = self._clock()
        with self._engine.begin() as connection:
            row = (
                connection.execute(
                    sa.select(user_sessions_table)
                    .where(user_sessions_table.c.session_token_hash == token_hash)
                    .where(user_sessions_table.c.expires_at > now)
                )
                .mappings()
                .one_or_none()
            )
        return cast_uuid(row["user_id"]) if row else None

    def delete(self, token: str) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                user_sessions_table.delete().where(
                    user_sessions_table.c.session_token_hash == hash_session_token(token)
                )
            )


def cast_uuid(value: object) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))
