"use client";

import type { DailyEntry } from "@/lib/types";

type EntryHistoryProps = {
  entries: DailyEntry[];
  monthLabel: string;
  onSelectDate: (entryDate: string) => Promise<void>;
  selectedEntry: DailyEntry | null;
};

export function EntryHistory({
  entries,
  monthLabel,
  onSelectDate,
  selectedEntry
}: EntryHistoryProps) {
  const entryDates = new Set(entries.map((entry) => entry.entry_date));
  const days = monthDays(entries[0]?.entry_date);

  return (
    <section className="card history-card" aria-labelledby="history-title">
      <div className="section-heading">
        <p className="eyebrow">History</p>
        <h2 id="history-title">{monthLabel}</h2>
      </div>
      <p className="muted">Saved days are marked with a little moon.</p>
      <div className="calendar-grid" role="list" aria-label={`${monthLabel} happy things history`}>
        {days.map((day) => {
          const hasEntry = entryDates.has(day.date);
          return (
            <button
              aria-label={`View happy things for ${day.date}`}
              className={hasEntry ? "calendar-day has-entry" : "calendar-day"}
              disabled={!hasEntry}
              key={day.date}
              onClick={() => onSelectDate(day.date)}
              type="button"
            >
              <span>{day.day}</span>
              {hasEntry ? <span aria-hidden="true">☾</span> : null}
            </button>
          );
        })}
      </div>

      {selectedEntry ? (
        <article className="selected-entry" aria-label={`Happy things for ${selectedEntry.entry_date}`}>
          <h3>{selectedEntry.entry_date}</h3>
          <ul>
            {selectedEntry.happy_items.map((item) => (
              <li key={item.id}>{item.content}</li>
            ))}
          </ul>
          <p>Encouragement score: {selectedEntry.encouragement_score}/5</p>
        </article>
      ) : (
        <p className="empty-history">Choose a marked day to revisit its three small happy things.</p>
      )}
    </section>
  );
}

function monthDays(firstEntryDate?: string): Array<{ date: string; day: number }> {
  const now = firstEntryDate ? new Date(`${firstEntryDate}T00:00:00`) : new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const dayCount = new Date(year, month + 1, 0).getDate();

  return Array.from({ length: dayCount }, (_, index) => {
    const day = index + 1;
    const date = new Date(year, month, day);
    return {
      date: [
        date.getFullYear(),
        String(date.getMonth() + 1).padStart(2, "0"),
        String(date.getDate()).padStart(2, "0")
      ].join("-"),
      day
    };
  });
}
