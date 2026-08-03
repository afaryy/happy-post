import { beforeEach, describe, expect, it, vi } from "vitest";

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
import type { CurrentUser, DailyEntry } from "@/lib/types";

const fetchMock = vi.fn();

vi.stubGlobal("fetch", fetchMock);

const entry: DailyEntry = {
  id: "entry-1",
  entry_date: "2026-08-03",
  user_id: "local",
  happy_items: [
    { id: "item-1", item_no: 1, content: "Warm tea", created_at: "2026-08-03T10:00:00Z" },
    { id: "item-2", item_no: 2, content: "Soft socks", created_at: "2026-08-03T10:00:00Z" },
    { id: "item-3", item_no: 3, content: "Moonlight", created_at: "2026-08-03T10:00:00Z" }
  ],
  encouragement_score: 4,
  created_at: "2026-08-03T10:00:00Z",
  updated_at: "2026-08-03T10:00:00Z"
};

const user: CurrentUser = {
  id: "25b8f9fd-5073-40a1-b645-810d6346458a",
  email: "dreamer@example.com",
  created_at: "2026-08-03T10:00:00Z",
  updated_at: "2026-08-03T10:00:00Z"
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

describe("daily entries API client", () => {
  beforeEach(() => {
    fetchMock.mockReset();
  });

  it("loads today's entry from the relative API path", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(entry));

    await expect(getTodayEntry()).resolves.toEqual(entry);
    expect(fetchMock).toHaveBeenCalledWith("/api/entries/today", { cache: "no-store" });
  });

  it("returns null when today's entry does not exist yet", async () => {
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 404 }));

    await expect(getTodayEntry()).resolves.toBeNull();
  });

  it("saves today's three happy things with a JSON payload", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(entry));

    await expect(
      saveTodayEntry({
        happy_items: ["Warm tea", "Soft socks", "Moonlight"],
        encouragement_score: 4
      })
    ).resolves.toEqual(entry);
    expect(fetchMock).toHaveBeenCalledWith("/api/entries/today", {
      body: JSON.stringify({
        happy_items: ["Warm tea", "Soft socks", "Moonlight"],
        encouragement_score: 4
      }),
      headers: { "Content-Type": "application/json" },
      method: "PUT"
    });
  });

  it("lists month entries from the relative API path", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse([entry]));

    await expect(listMonthEntries("2026-08")).resolves.toEqual([entry]);
    expect(fetchMock).toHaveBeenCalledWith("/api/entries?month=2026-08", { cache: "no-store" });
  });

  it("loads an entry by date from the relative API path", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(entry));

    await expect(getEntryByDate("2026-08-03")).resolves.toEqual(entry);
    expect(fetchMock).toHaveBeenCalledWith("/api/entries/2026-08-03", { cache: "no-store" });
  });

  it("throws a safe error when saving fails", async () => {
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 500 }));

    await expect(
      saveTodayEntry({
        happy_items: ["Warm tea", "Soft socks", "Moonlight"],
        encouragement_score: 4
      })
    ).rejects.toThrow("Unable to save tonight's happy things");
  });

  it("signs up with email and password", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(user, 201));

    await expect(signup("dreamer@example.com", "warm-password-123")).resolves.toEqual(user);
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/signup", {
      body: JSON.stringify({ email: "dreamer@example.com", password: "warm-password-123" }),
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      method: "POST"
    });
  });

  it("signs in with email and password", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(user));

    await expect(signin("dreamer@example.com", "warm-password-123")).resolves.toEqual(user);
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/signin", {
      body: JSON.stringify({ email: "dreamer@example.com", password: "warm-password-123" }),
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      method: "POST"
    });
  });

  it("loads the current signed-in user and returns null when signed out", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(user));
    await expect(getCurrentUser()).resolves.toEqual(user);
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/me", {
      cache: "no-store",
      credentials: "include"
    });

    fetchMock.mockResolvedValueOnce(new Response(null, { status: 401 }));
    await expect(getCurrentUser()).resolves.toBeNull();
  });

  it("signs out through the auth API", async () => {
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }));

    await expect(signout()).resolves.toBeUndefined();
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/signout", {
      credentials: "include",
      method: "POST"
    });
  });
});
