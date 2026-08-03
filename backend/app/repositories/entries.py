from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Protocol
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.engine import Engine, RowMapping

from app.db.models import daily_entries_table, daily_entry_items_table
from app.domain.entries import DailyEntry, DailyEntryItem, SaveDailyEntry


class DailyEntryRepository(Protocol):
    def save(self, user_id: UUID, entry_date: date, payload: SaveDailyEntry) -> DailyEntry: ...

    def get(self, user_id: UUID, entry_date: date) -> DailyEntry | None: ...

    def list_month(self, user_id: UUID, year: int, month: int) -> list[DailyEntry]: ...


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def row_to_item(row: RowMapping) -> DailyEntryItem:
    return DailyEntryItem(
        id=row["id"],
        item_no=row["item_no"],
        content=row["content"],
        created_at=ensure_aware(row["created_at"]),
    )


def row_to_entry(row: RowMapping, items: list[DailyEntryItem]) -> DailyEntry:
    return DailyEntry(
        id=row["id"],
        user_id=row["user_id"],
        entry_date=row["entry_date"],
        happy_items=items,
        encouragement_score=row["encouragement_score"],
        created_at=ensure_aware(row["created_at"]),
        updated_at=ensure_aware(row["updated_at"]),
    )


class InMemoryDailyEntryRepository:
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or utc_now
        self._entries: dict[tuple[UUID, date], DailyEntry] = {}

    def save(self, user_id: UUID, entry_date: date, payload: SaveDailyEntry) -> DailyEntry:
        now = self._clock()
        key = (user_id, entry_date)
        existing = self._entries.get(key)
        entry = DailyEntry(
            id=existing.id if existing else uuid4(),
            user_id=user_id,
            entry_date=entry_date,
            happy_items=[
                DailyEntryItem(id=uuid4(), item_no=index, content=content, created_at=now)
                for index, content in enumerate(payload.happy_items, start=1)
            ],
            encouragement_score=payload.encouragement_score,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        self._entries[key] = entry
        return entry

    def get(self, user_id: UUID, entry_date: date) -> DailyEntry | None:
        return self._entries.get((user_id, entry_date))

    def list_month(self, user_id: UUID, year: int, month: int) -> list[DailyEntry]:
        return sorted(
            [
                entry
                for entry in self._entries.values()
                if entry.user_id == user_id
                and entry.entry_date.year == year
                and entry.entry_date.month == month
            ],
            key=lambda entry: entry.entry_date,
            reverse=True,
        )


class SqlAlchemyDailyEntryRepository:
    def __init__(self, engine: Engine, clock: Callable[[], datetime] | None = None) -> None:
        self._engine = engine
        self._clock = clock or utc_now

    def save(self, user_id: UUID, entry_date: date, payload: SaveDailyEntry) -> DailyEntry:
        now = self._clock()
        with self._engine.begin() as connection:
            existing = connection.execute(
                sa.select(daily_entries_table)
                .where(daily_entries_table.c.user_id == user_id)
                .where(daily_entries_table.c.entry_date == entry_date)
            ).mappings().one_or_none()
            if existing is None:
                entry_id = uuid4()
                connection.execute(
                    daily_entries_table.insert().values(
                        id=entry_id,
                        user_id=user_id,
                        entry_date=entry_date,
                        encouragement_score=payload.encouragement_score,
                        created_at=now,
                        updated_at=now,
                    )
                )
            else:
                entry_id = cast_uuid(existing["id"])
                connection.execute(
                    daily_entries_table.update()
                    .where(daily_entries_table.c.entry_date == entry_date)
                    .where(daily_entries_table.c.user_id == user_id)
                    .values(
                        encouragement_score=payload.encouragement_score,
                        updated_at=now,
                    )
                )
                connection.execute(
                    daily_entry_items_table.delete().where(
                        daily_entry_items_table.c.entry_id == entry_id
                    )
                )

            connection.execute(
                daily_entry_items_table.insert(),
                [
                    {
                        "id": uuid4(),
                        "entry_id": entry_id,
                        "item_no": index,
                        "content": content,
                        "created_at": now,
                    }
                    for index, content in enumerate(payload.happy_items, start=1)
                ],
            )

            saved = connection.execute(
                sa.select(daily_entries_table).where(daily_entries_table.c.id == entry_id)
            ).mappings().one()
            item_rows = (
                connection.execute(
                    sa.select(daily_entry_items_table)
                    .where(daily_entry_items_table.c.entry_id == entry_id)
                    .order_by(daily_entry_items_table.c.item_no.asc())
                )
                .mappings()
                .all()
            )
        return row_to_entry(saved, [row_to_item(row) for row in item_rows])

    def get(self, user_id: UUID, entry_date: date) -> DailyEntry | None:
        with self._engine.begin() as connection:
            row = connection.execute(
                sa.select(daily_entries_table)
                .where(daily_entries_table.c.user_id == user_id)
                .where(daily_entries_table.c.entry_date == entry_date)
            ).mappings().one_or_none()
            item_rows = []
            if row:
                item_rows = (
                    connection.execute(
                        sa.select(daily_entry_items_table)
                        .where(daily_entry_items_table.c.entry_id == row["id"])
                        .order_by(daily_entry_items_table.c.item_no.asc())
                    )
                    .mappings()
                    .all()
                )
        return row_to_entry(row, [row_to_item(item_row) for item_row in item_rows]) if row else None

    def list_month(self, user_id: UUID, year: int, month: int) -> list[DailyEntry]:
        start = date(year, month, 1)
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        with self._engine.begin() as connection:
            rows = (
                connection.execute(
                    sa.select(daily_entries_table)
                    .where(daily_entries_table.c.user_id == user_id)
                    .where(daily_entries_table.c.entry_date >= start)
                    .where(daily_entries_table.c.entry_date < end)
                    .order_by(daily_entries_table.c.entry_date.desc())
                )
                .mappings()
                .all()
            )
            item_rows = (
                connection.execute(
                    sa.select(daily_entry_items_table)
                    .where(
                        daily_entry_items_table.c.entry_id.in_(
                            [row["id"] for row in rows] or [uuid4()]
                        )
                    )
                    .order_by(
                        daily_entry_items_table.c.entry_id.asc(),
                        daily_entry_items_table.c.item_no.asc(),
                    )
                )
                .mappings()
                .all()
            )
        items_by_entry: dict[UUID, list[DailyEntryItem]] = {}
        for item_row in item_rows:
            items_by_entry.setdefault(cast_uuid(item_row["entry_id"]), []).append(
                row_to_item(item_row)
            )
        return [row_to_entry(row, items_by_entry.get(cast_uuid(row["id"]), [])) for row in rows]


def cast_uuid(value: object) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))
