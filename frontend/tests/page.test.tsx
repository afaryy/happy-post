import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Page from "@/app/page";
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

vi.mock("@/lib/api", () => ({
  getCurrentUser: vi.fn(),
  getEntryByDate: vi.fn(),
  getTodayEntry: vi.fn(),
  listMonthEntries: vi.fn(),
  saveTodayEntry: vi.fn(),
  signin: vi.fn(),
  signout: vi.fn(),
  signup: vi.fn()
}));

const currentUser: CurrentUser = {
  id: "25b8f9fd-5073-40a1-b645-810d6346458a",
  email: "dreamer@example.com",
  created_at: "2026-08-03T10:00:00Z",
  updated_at: "2026-08-03T10:00:00Z"
};

const todayEntry: DailyEntry = {
  id: "entry-1",
  entry_date: "2026-08-03",
  user_id: "local",
  happy_items: [
    { id: "item-1", item_no: 1, content: "Warm tea before bed", created_at: "2026-08-03T10:00:00Z" },
    { id: "item-2", item_no: 2, content: "A funny message from a friend", created_at: "2026-08-03T10:00:00Z" },
    { id: "item-3", item_no: 3, content: "The sky looked soft tonight", created_at: "2026-08-03T10:00:00Z" }
  ],
  encouragement_score: 4,
  created_at: "2026-08-03T10:00:00Z",
  updated_at: "2026-08-03T10:00:00Z"
};

describe("Three small happy things page", () => {
  beforeEach(() => {
    vi.setSystemTime(new Date("2026-08-03T12:00:00Z"));
    vi.mocked(getCurrentUser).mockReset();
    vi.mocked(getEntryByDate).mockReset();
    vi.mocked(getTodayEntry).mockReset();
    vi.mocked(listMonthEntries).mockReset();
    vi.mocked(saveTodayEntry).mockReset();
    vi.mocked(signin).mockReset();
    vi.mocked(signout).mockReset();
    vi.mocked(signup).mockReset();
    vi.mocked(getCurrentUser).mockResolvedValue(currentUser);
    vi.mocked(getTodayEntry).mockResolvedValue(null);
    vi.mocked(listMonthEntries).mockResolvedValue([]);
  });

  it("shows a gentle sign-in form before loading private happy things", async () => {
    vi.mocked(getCurrentUser).mockResolvedValueOnce(null);

    render(<Page />);

    expect(await screen.findByText("Sign in to your Happy Post")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(getTodayEntry).not.toHaveBeenCalled();
  });

  it("signs in and then loads the user's happy things", async () => {
    const user = userEvent.setup();
    vi.mocked(getCurrentUser).mockResolvedValueOnce(null);
    vi.mocked(signin).mockResolvedValueOnce(currentUser);

    render(<Page />);
    await user.type(await screen.findByLabelText("Email"), "dreamer@example.com");
    await user.type(screen.getByLabelText("Password"), "warm-password-123");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(signin).toHaveBeenCalledWith("dreamer@example.com", "warm-password-123");
    expect(await screen.findByText("Three small happy things")).toBeInTheDocument();
    expect(getTodayEntry).toHaveBeenCalled();
  });

  it("invites the user to start with three small happy things", async () => {
    render(<Page />);

    expect(await screen.findByText("Three small happy things")).toBeInTheDocument();
    expect(screen.getByLabelText("First small happy thing")).toBeInTheDocument();
    expect(screen.getByLabelText("Second small happy thing")).toBeInTheDocument();
    expect(screen.getByLabelText("Third small happy thing")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save my happy things" })).toBeDisabled();
  });

  it("loads an existing today entry into the form", async () => {
    vi.mocked(getTodayEntry).mockResolvedValueOnce(todayEntry);
    vi.mocked(listMonthEntries).mockResolvedValueOnce([todayEntry]);

    render(<Page />);

    expect(await screen.findByDisplayValue("Warm tea before bed")).toBeInTheDocument();
    expect(screen.getByDisplayValue("A funny message from a friend")).toBeInTheDocument();
    expect(screen.getByDisplayValue("The sky looked soft tonight")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "4" })).toBeChecked();
  });

  it("saves at least three happy things and shows a warm success message", async () => {
    const user = userEvent.setup();
    vi.mocked(saveTodayEntry).mockResolvedValueOnce(todayEntry);
    vi.mocked(listMonthEntries).mockResolvedValueOnce([]);

    render(<Page />);
    await screen.findByText("Three small happy things");
    await user.type(screen.getByLabelText("First small happy thing"), "Warm tea before bed");
    await user.type(
      screen.getByLabelText("Second small happy thing"),
      "A funny message from a friend"
    );
    await user.type(
      screen.getByLabelText("Third small happy thing"),
      "The sky looked soft tonight"
    );
    await user.click(screen.getByRole("radio", { name: "4" }));
    await user.click(screen.getByRole("button", { name: "Save my happy things" }));

    expect(saveTodayEntry).toHaveBeenCalledWith({
      happy_items: [
        "Warm tea before bed",
        "A funny message from a friend",
        "The sky looked soft tonight"
      ],
      encouragement_score: 4
    });
    expect(await screen.findByText(/Three little lights from today are saved/)).toBeInTheDocument();
  });

  it("allows the user to add another happy thing", async () => {
    const user = userEvent.setup();
    vi.mocked(saveTodayEntry).mockResolvedValueOnce({
      ...todayEntry,
      happy_items: [
        ...todayEntry.happy_items,
        {
          id: "item-4",
          item_no: 4,
          content: "One extra sparkle",
          created_at: "2026-08-03T10:00:00Z"
        }
      ]
    });

    render(<Page />);
    await screen.findByText("Three small happy things");
    await user.type(screen.getByLabelText("First small happy thing"), "Warm tea before bed");
    await user.type(
      screen.getByLabelText("Second small happy thing"),
      "A funny message from a friend"
    );
    await user.type(
      screen.getByLabelText("Third small happy thing"),
      "The sky looked soft tonight"
    );
    await user.click(screen.getByRole("button", { name: "Add another happy thing" }));
    await user.type(screen.getByLabelText("Happy thing 4"), "One extra sparkle");
    await user.click(screen.getByRole("button", { name: "Save my happy things" }));

    expect(saveTodayEntry).toHaveBeenCalledWith({
      happy_items: [
        "Warm tea before bed",
        "A funny message from a friend",
        "The sky looked soft tonight",
        "One extra sparkle"
      ],
      encouragement_score: 3
    });
  });

  it("marks saved days in the monthly history calendar", async () => {
    vi.mocked(listMonthEntries).mockResolvedValueOnce([todayEntry]);
    vi.mocked(getEntryByDate).mockResolvedValueOnce(todayEntry);
    const user = userEvent.setup();

    render(<Page />);
    await screen.findByText("August 2026");
    await user.click(screen.getByRole("button", { name: "View happy things for 2026-08-03" }));

    expect(await screen.findByText("Warm tea before bed")).toBeInTheDocument();
    expect(screen.getByText("Encouragement score: 4/5")).toBeInTheDocument();
  });

  it("shows a gentle error when saving fails", async () => {
    const user = userEvent.setup();
    vi.mocked(saveTodayEntry).mockRejectedValueOnce(new Error("failed"));

    render(<Page />);
    await screen.findByText("Three small happy things");
    await user.type(screen.getByLabelText("First small happy thing"), "Warm tea");
    await user.type(screen.getByLabelText("Second small happy thing"), "Soft socks");
    await user.type(screen.getByLabelText("Third small happy thing"), "Moonlight");
    await user.click(screen.getByRole("button", { name: "Save my happy things" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn’t save just now. Please try again."
    );
  });
});
