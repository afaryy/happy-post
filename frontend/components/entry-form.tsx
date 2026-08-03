"use client";

import { FormEvent } from "react";

import type { DailyEntry, SaveDailyEntryInput } from "@/lib/types";

type EntryFormProps = {
  form: SaveDailyEntryInput;
  isSubmitting: boolean;
  onChange: (form: SaveDailyEntryInput) => void;
  onSubmit: () => Promise<void>;
  todayEntry: DailyEntry | null;
};

const prompts = [
  {
    label: "First small happy thing",
    placeholder: "A tiny moment that made me smile"
  },
  {
    label: "Second small happy thing",
    placeholder: "Something warm, kind, or funny"
  },
  {
    label: "Third small happy thing",
    placeholder: "One gentle little light from today"
  }
] as const;

const scoreLabels = ["1", "2", "3", "4", "5"] as const;

export function EntryForm({ form, isSubmitting, onChange, onSubmit, todayEntry }: EntryFormProps) {
  const canSubmit =
    form.happy_items.length >= 3 &&
    form.happy_items.every((item) => item.trim().length > 0) &&
    !isSubmitting;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }
    await onSubmit();
  }

  return (
    <section className="card hero-card" aria-labelledby="tonight-title">
      <p className="eyebrow">Bedtime reflection</p>
      <h1 id="tonight-title">Three small happy things</h1>
      <p className="intro">
        Before sleep, find at least three tiny happy things from today. Add more if they come to mind.
      </p>

      <form className="entry-form" onSubmit={handleSubmit}>
        {form.happy_items.map((happyItem, index) => (
          <label className="happy-field" key={index}>
            <span>{prompts[index]?.label ?? `Happy thing ${index + 1}`}</span>
            <textarea
              maxLength={180}
              onChange={(event) =>
                onChange({
                  ...form,
                  happy_items: form.happy_items.map((item, itemIndex) =>
                    itemIndex === index ? event.target.value : item
                  )
                })
              }
              placeholder={prompts[index]?.placeholder ?? "Another small happy thing"}
              rows={2}
              value={happyItem}
            />
          </label>
        ))}

        <button
          className="secondary-button"
          disabled={form.happy_items.length >= 10}
          onClick={() => onChange({ ...form, happy_items: [...form.happy_items, ""] })}
          type="button"
        >
          Add another happy thing
        </button>

        <fieldset className="score-picker">
          <legend>Encouragement score</legend>
          <p>How much did these three little lights help tonight?</p>
          <div className="score-options">
            {scoreLabels.map((score) => (
              <label key={score}>
                <input
                  checked={form.encouragement_score === Number(score)}
                  name="encouragement_score"
                  onChange={() =>
                    onChange({
                      ...form,
                      encouragement_score: Number(score)
                    })
                  }
                  type="radio"
                  value={score}
                />
                <span>{score}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <button className="primary-button" disabled={!canSubmit} type="submit">
          {isSubmitting ? "Saving…" : "Save my happy things"}
        </button>
      </form>

      {todayEntry ? (
        <p className="saved-note">Tonight has happy things saved. ✨</p>
      ) : null}
    </section>
  );
}
