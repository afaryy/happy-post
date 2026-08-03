from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

HAPPY_THING_MAX_LENGTH = 180
HAPPY_ITEMS_MIN_COUNT = 3
HAPPY_ITEMS_MAX_COUNT = 10


class SaveDailyEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    happy_items: list[str] = Field(
        min_length=HAPPY_ITEMS_MIN_COUNT, max_length=HAPPY_ITEMS_MAX_COUNT
    )
    encouragement_score: int = Field(ge=1, le=5)

    @field_validator("happy_items")
    @classmethod
    def happy_items_must_be_small_and_present(cls, values: list[str]) -> list[str]:
        happy_items = [value.strip() for value in values]
        if any(not value for value in happy_items):
            raise ValueError("happy items must not be blank")
        if any(len(value) > HAPPY_THING_MAX_LENGTH for value in happy_items):
            raise ValueError(f"happy items must be {HAPPY_THING_MAX_LENGTH} characters or fewer")
        return happy_items


class DailyEntryItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    item_no: int
    content: str
    created_at: datetime


class DailyEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    user_id: UUID
    entry_date: date
    happy_items: list[DailyEntryItem]
    encouragement_score: int
    created_at: datetime
    updated_at: datetime
