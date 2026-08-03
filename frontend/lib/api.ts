import type { CurrentUser, DailyEntry, SaveDailyEntryInput } from "@/lib/types";

async function requireSuccess(response: Response, message: string): Promise<Response> {
  if (!response.ok) {
    throw new Error(message);
  }
  return response;
}

export async function getTodayEntry(): Promise<DailyEntry | null> {
  const response = await fetch("/api/entries/today", { cache: "no-store" });
  if (response.status === 404) {
    return null;
  }
  return requireSuccess(response, "Unable to load tonight's happy things").then((result) =>
    result.json()
  );
}

export async function saveTodayEntry(input: SaveDailyEntryInput): Promise<DailyEntry> {
  const response = await fetch("/api/entries/today", {
    body: JSON.stringify(input),
    headers: { "Content-Type": "application/json" },
    method: "PUT"
  });
  return requireSuccess(response, "Unable to save tonight's happy things").then((result) =>
    result.json()
  );
}

export async function listMonthEntries(month: string): Promise<DailyEntry[]> {
  const response = await fetch(`/api/entries?month=${month}`, { cache: "no-store" });
  return requireSuccess(response, "Unable to load happy things history").then((result) =>
    result.json()
  );
}

export async function getEntryByDate(entryDate: string): Promise<DailyEntry | null> {
  const response = await fetch(`/api/entries/${entryDate}`, { cache: "no-store" });
  if (response.status === 404) {
    return null;
  }
  return requireSuccess(response, "Unable to load this day's happy things").then((result) =>
    result.json()
  );
}

export async function signup(email: string, password: string): Promise<CurrentUser> {
  const response = await fetch("/api/auth/signup", {
    body: JSON.stringify({ email, password }),
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    method: "POST"
  });
  return requireSuccess(response, "Unable to create your Happy Post account").then((result) =>
    result.json()
  );
}

export async function signin(email: string, password: string): Promise<CurrentUser> {
  const response = await fetch("/api/auth/signin", {
    body: JSON.stringify({ email, password }),
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    method: "POST"
  });
  return requireSuccess(response, "Unable to sign in to Happy Post").then((result) =>
    result.json()
  );
}

export async function signout(): Promise<void> {
  const response = await fetch("/api/auth/signout", {
    credentials: "include",
    method: "POST"
  });
  await requireSuccess(response, "Unable to sign out");
}

export async function getCurrentUser(): Promise<CurrentUser | null> {
  const response = await fetch("/api/auth/me", {
    cache: "no-store",
    credentials: "include"
  });
  if (response.status === 401) {
    return null;
  }
  return requireSuccess(response, "Unable to load your Happy Post account").then((result) =>
    result.json()
  );
}
