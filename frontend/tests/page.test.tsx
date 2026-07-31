import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Page from "@/app/page";
import { createPost, listPosts } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  createPost: vi.fn(),
  listPosts: vi.fn()
}));

const firstPost = {
  id: "post-1",
  message: "First",
  created_at: "2026-07-31T10:00:00Z"
};

const secondPost = {
  id: "post-2",
  message: "Second",
  created_at: "2026-07-31T10:01:00Z"
};

describe("Happy Post board", () => {
  beforeEach(() => {
    vi.mocked(createPost).mockReset();
    vi.mocked(listPosts).mockReset();
  });

  it("shows a loading state before the posts request completes", () => {
    vi.mocked(listPosts).mockReturnValue(new Promise(() => undefined));

    render(<Page />);

    expect(screen.getByText("Loading posts…")).toBeInTheDocument();
  });

  it("shows an empty state after loading no posts", async () => {
    vi.mocked(listPosts).mockResolvedValueOnce([]);

    render(<Page />);

    expect(await screen.findByText("No posts yet.")).toBeInTheDocument();
  });

  it("adds a created post to the top of the list", async () => {
    const user = userEvent.setup();
    vi.mocked(listPosts).mockResolvedValueOnce([firstPost]);
    vi.mocked(createPost).mockResolvedValueOnce(secondPost);

    render(<Page />);
    await screen.findByText("First");
    await user.type(screen.getByLabelText("Message"), "Second");
    await user.click(screen.getByRole("button", { name: "Post" }));

    expect(await screen.findByText("Second")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      "Second",
      "First"
    ]);
  });

  it("disables submission for a blank message", async () => {
    const user = userEvent.setup();
    vi.mocked(listPosts).mockResolvedValueOnce([]);

    render(<Page />);
    await screen.findByText("No posts yet.");
    await user.type(screen.getByLabelText("Message"), "   ");

    expect(screen.getByRole("button", { name: "Post" })).toBeDisabled();
  });

  it("shows an error when loading posts fails", async () => {
    vi.mocked(listPosts).mockRejectedValueOnce(new Error("Unable to load posts"));

    render(<Page />);

    expect(await screen.findByText("Unable to load posts.")).toBeInTheDocument();
  });
});
