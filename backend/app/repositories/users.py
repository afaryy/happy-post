from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.engine import Engine, RowMapping

from app.db.models import users_table
from app.domain.auth import CurrentUser


class UserRepository(Protocol):
    def create(self, email: str, password_hash: str) -> CurrentUser: ...

    def get_by_email(self, email: str) -> tuple[CurrentUser, str] | None: ...

    def get_by_id(self, user_id: UUID) -> CurrentUser | None: ...


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def row_to_user(row: RowMapping) -> CurrentUser:
    return CurrentUser(
        id=cast_uuid(row["id"]),
        email=row["email"],
        created_at=ensure_aware(row["created_at"]),
        updated_at=ensure_aware(row["updated_at"]),
    )


class DuplicateEmailError(ValueError):
    pass


class InMemoryUserRepository:
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or utc_now
        self._users_by_email: dict[str, tuple[CurrentUser, str]] = {}

    def create(self, email: str, password_hash: str) -> CurrentUser:
        if email in self._users_by_email:
            raise DuplicateEmailError(email)
        now = self._clock()
        user = CurrentUser(id=uuid4(), email=email, created_at=now, updated_at=now)
        self._users_by_email[email] = (user, password_hash)
        return user

    def get_by_email(self, email: str) -> tuple[CurrentUser, str] | None:
        return self._users_by_email.get(email)

    def get_by_id(self, user_id: UUID) -> CurrentUser | None:
        for user, _password_hash in self._users_by_email.values():
            if user.id == user_id:
                return user
        return None


class SqlAlchemyUserRepository:
    def __init__(self, engine: Engine, clock: Callable[[], datetime] | None = None) -> None:
        self._engine = engine
        self._clock = clock or utc_now

    def create(self, email: str, password_hash: str) -> CurrentUser:
        now = self._clock()
        user_id = uuid4()
        try:
            with self._engine.begin() as connection:
                connection.execute(
                    users_table.insert().values(
                        id=user_id,
                        email=email,
                        password_hash=password_hash,
                        created_at=now,
                        updated_at=now,
                    )
                )
        except sa.exc.IntegrityError as exc:
            raise DuplicateEmailError(email) from exc
        user = self.get_by_id(user_id)
        if user is None:
            raise RuntimeError("created user could not be loaded")
        return user

    def get_by_email(self, email: str) -> tuple[CurrentUser, str] | None:
        with self._engine.begin() as connection:
            row = (
                connection.execute(sa.select(users_table).where(users_table.c.email == email))
                .mappings()
                .one_or_none()
            )
        return (row_to_user(row), row["password_hash"]) if row else None

    def get_by_id(self, user_id: UUID) -> CurrentUser | None:
        with self._engine.begin() as connection:
            row = (
                connection.execute(sa.select(users_table).where(users_table.c.id == user_id))
                .mappings()
                .one_or_none()
            )
        return row_to_user(row) if row else None


def cast_uuid(value: object) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))
