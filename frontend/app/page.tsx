"use client";

import { useEffect, useMemo, useState } from "react";

import { AuthPanel } from "@/components/auth-panel";
import { EntryForm } from "@/components/entry-form";
import { EntryHistory } from "@/components/entry-history";
import {
  getCurrentUser,
  getEntryByDate,
  getTodayEntry,
  listMonthEntries,
  saveTodayEntry,
  signin,
  signout,
  signup
} from "@/lib/api";
import type { CurrentUser, DailyEntry, SaveDailyEntryInput } from "@/lib/types";

const emptyForm: SaveDailyEntryInput = {
  happy_items: ["", "", ""],
  encouragement_score: 3
};

export default function Page() {
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [form, setForm] = useState<SaveDailyEntryInput>(emptyForm);
  const [todayEntry, setTodayEntry] = useState<DailyEntry | null>(null);
  const [monthEntries, setMonthEntries] = useState<DailyEntry[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<DailyEntry | null>(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [isAuthSubmitting, setIsAuthSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const month = useMemo(() => currentMonth(), []);
  const monthLabel = useMemo(() => monthName(month), [month]);

  useEffect(() => {
    let active = true;

    async function loadCurrentUser() {
      try {
        const loadedUser = await getCurrentUser();
        if (active) {
          setIsLoading(loadedUser !== null);
          setCurrentUser(loadedUser);
        }
      } catch {
        if (active) {
          setAuthError("Couldn’t check your Happy Post sign-in just now.");
        }
      } finally {
        if (active) {
          setIsAuthLoading(false);
        }
      }
    }

    void loadCurrentUser();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!currentUser) {
      return;
    }

    let active = true;

    async function loadEntries() {
      try {
        const [loadedTodayEntry, loadedMonthEntries] = await Promise.all([
          getTodayEntry(),
          listMonthEntries(month)
        ]);
        if (!active) {
          return;
        }
        setTodayEntry(loadedTodayEntry);
        setMonthEntries(loadedMonthEntries);
        if (loadedTodayEntry) {
          setForm(entryToForm(loadedTodayEntry));
        }
      } catch {
        if (active) {
          setError("Couldn’t load your three happy things just now.");
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void loadEntries();

    return () => {
      active = false;
    };
  }, [currentUser, month]);

  function resetEntryState(nextLoadingState: boolean) {
    setForm(emptyForm);
    setTodayEntry(null);
    setMonthEntries([]);
    setSelectedEntry(null);
    setIsLoading(nextLoadingState);
    setError(null);
    setSuccessMessage(null);
  }

  async function handleSignin(email: string, password: string) {
    setIsAuthSubmitting(true);
    setAuthError(null);
    try {
      setCurrentUser(await signin(email, password));
      resetEntryState(true);
    } catch {
      setAuthError("That sign-in didn’t work. Please check your email and password.");
    } finally {
      setIsAuthSubmitting(false);
    }
  }

  async function handleSignup(email: string, password: string) {
    setIsAuthSubmitting(true);
    setAuthError(null);
    try {
      setCurrentUser(await signup(email, password));
      resetEntryState(true);
    } catch {
      setAuthError("Couldn’t create that Happy Post account just now.");
    } finally {
      setIsAuthSubmitting(false);
    }
  }

  async function handleSignout() {
    setError(null);
    setSuccessMessage(null);
    await signout();
    setCurrentUser(null);
    resetEntryState(false);
  }

  async function handleSave() {
    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const saved = await saveTodayEntry({
        happy_items: form.happy_items.map((item) => item.trim()),
        encouragement_score: form.encouragement_score
      });
      setTodayEntry(saved);
      setSelectedEntry(saved);
      setMonthEntries((entries) => mergeEntry(entries, saved));
      setSuccessMessage("Beautiful. Three little lights from today are saved. Sleep gently. 🌙");
    } catch {
      setError("Couldn’t save just now. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSelectDate(entryDate: string) {
    setError(null);
    try {
      setSelectedEntry(await getEntryByDate(entryDate));
    } catch {
      setError("Couldn’t open that day’s three happy things just now.");
    }
  }

  if (isAuthLoading) {
    return (
      <main>
        <div className="auth-shell">
          <p className="status">Opening your quiet bedtime space…</p>
        </div>
      </main>
    );
  }

  if (!currentUser) {
    return (
      <AuthPanel
        error={authError}
        isSubmitting={isAuthSubmitting}
        onSignin={handleSignin}
        onSignup={handleSignup}
      />
    );
  }

  return (
    <main>
      <div className="app-shell">
        <div className="moon-glow" aria-hidden="true" />
        <div className="user-bar">
          <span>Signed in as {currentUser.email}</span>
          <button className="link-button" onClick={handleSignout} type="button">
            Sign out
          </button>
        </div>
        <EntryForm
          form={form}
          isSubmitting={isSubmitting}
          onChange={setForm}
          onSubmit={handleSave}
          todayEntry={todayEntry}
        />

        <aside className="side-panel">
          {isLoading ? <p className="status">Warming up tonight’s page…</p> : null}
          {successMessage ? <p className="success-message">{successMessage}</p> : null}
          {error ? <p role="alert">{error}</p> : null}
          <EntryHistory
            entries={monthEntries}
            monthLabel={monthLabel}
            onSelectDate={handleSelectDate}
            selectedEntry={selectedEntry}
          />
        </aside>
      </div>
    </main>
  );
}

function entryToForm(entry: DailyEntry): SaveDailyEntryInput {
  return {
    happy_items: entry.happy_items.map((item) => item.content),
    encouragement_score: entry.encouragement_score
  };
}

function mergeEntry(entries: DailyEntry[], saved: DailyEntry): DailyEntry[] {
  const withoutSavedDay = entries.filter((entry) => entry.entry_date !== saved.entry_date);
  return [saved, ...withoutSavedDay].sort((left, right) =>
    right.entry_date.localeCompare(left.entry_date)
  );
}

function currentMonth(): string {
  const now = new Date();
  return [now.getFullYear(), String(now.getMonth() + 1).padStart(2, "0")].join("-");
}

function monthName(month: string): string {
  const [year, monthNumber] = month.split("-").map(Number);
  return new Intl.DateTimeFormat("en-AU", {
    month: "long",
    year: "numeric"
  }).format(new Date(year, monthNumber - 1, 1));
}
