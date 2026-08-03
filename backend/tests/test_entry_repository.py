from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
import sqlalchemy as sa
from pydantic import ValidationError

from app.db.models import metadata
from app.domain.entries import SaveDailyEntry
from app.repositories.entries import InMemoryDailyEntryRepository, SqlAlchemyDailyEntryRepository


def valid_entry() -> SaveDailyEntry:
    return SaveDailyEntry(
        happy_items=[
            "A sleepy cat in the window",
            "A kind wave from a neighbour",
            "The first sip of tea",
        ],
        encouragement_score=4,
    )


def test_save_daily_entry_trims_happy_things() -> None:
    entry = SaveDailyEntry(
        happy_items=["  soft rain  ", " warm socks ", "  quiet music"],
        encouragement_score=3,
    )

    assert entry.happy_items == ["soft rain", "warm socks", "quiet music"]


def test_save_daily_entry_requires_three_small_happy_things() -> None:
    with pytest.raises(ValidationError):
        SaveDailyEntry(
            happy_items=["", "warm socks", "quiet music"],
            encouragement_score=3,
        )


def test_save_daily_entry_rejects_score_outside_one_to_five() -> None:
    with pytest.raises(ValidationError):
        SaveDailyEntry(
            happy_items=["soft rain", "warm socks", "quiet music"],
            encouragement_score=6,
        )


def test_in_memory_repository_updates_one_entry_per_day() -> None:
    now = datetime(2026, 8, 3, 10, 0, tzinfo=UTC)
    repository = InMemoryDailyEntryRepository(clock=lambda: now)
    user_id = uuid4()

    first = repository.save(user_id, date(2026, 8, 3), valid_entry())
    second = repository.save(
        user_id,
        date(2026, 8, 3),
        SaveDailyEntry(
            happy_items=["Fresh sheets", "Moonlight", "A calm walk", "One extra sparkle"],
            encouragement_score=5,
        ),
    )

    assert second.id == first.id
    assert [item.content for item in second.happy_items] == [
        "Fresh sheets",
        "Moonlight",
        "A calm walk",
        "One extra sparkle",
    ]
    assert repository.list_month(user_id, 2026, 8) == [second]


def test_sqlalchemy_repository_persists_and_lists_month_entries() -> None:
    engine = sa.create_engine("sqlite+pysqlite:///:memory:", future=True)
    metadata.create_all(engine)
    timestamps = iter(
        [
            datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
            datetime(2026, 8, 2, 10, 0, tzinfo=UTC),
        ]
    )
    repository = SqlAlchemyDailyEntryRepository(engine, clock=lambda: next(timestamps))
    user_id = uuid4()

    older = repository.save(user_id, date(2026, 8, 1), valid_entry())
    newer = repository.save(
        user_id,
        date(2026, 8, 2),
        SaveDailyEntry(
            happy_items=["Golden toast", "A soft jumper", "A tiny joke"],
            encouragement_score=5,
        ),
    )

    assert repository.get(user_id, date(2026, 8, 1)) == older
    assert repository.get(user_id, date(2026, 8, 2)) == newer
    assert repository.list_month(user_id, 2026, 8) == [newer, older]


def test_sqlalchemy_repository_updates_existing_entry() -> None:
    engine = sa.create_engine("sqlite+pysqlite:///:memory:", future=True)
    metadata.create_all(engine)
    timestamps = iter(
        [
            datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
            datetime(2026, 8, 1, 10, 5, tzinfo=UTC),
        ]
    )
    repository = SqlAlchemyDailyEntryRepository(engine, clock=lambda: next(timestamps))
    user_id = uuid4()

    first = repository.save(user_id, date(2026, 8, 1), valid_entry())
    updated = repository.save(
        user_id,
        date(2026, 8, 1),
        SaveDailyEntry(
            happy_items=["A blue cup", "Clean pyjamas", "A gentle song", "One bonus smile"],
            encouragement_score=5,
        ),
    )

    assert updated.id == first.id
    assert updated.created_at == first.created_at
    assert updated.updated_at == datetime(2026, 8, 1, 10, 5, tzinfo=UTC)
    assert [item.content for item in updated.happy_items] == [
        "A blue cup",
        "Clean pyjamas",
        "A gentle song",
        "One bonus smile",
    ]
    assert repository.list_month(user_id, 2026, 8) == [updated]
