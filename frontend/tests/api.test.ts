import { beforeEach, describe, expect, it, vi } from "vitest";

import { createPost, listPosts } from "@/lib/api";

const fetchMock = vi.fn();

vi.stubGlobal("fetch", fetchMock);

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

describe("posts API client", () => {
  beforeEach(() => {
    fetchMock.mockReset();
  });

  it("lists posts from the relative API path", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse([]));

    await expect(listPosts()).resolves.toEqual([]);
    expect(fetchMock).toHaveBeenCalledWith("/api/posts", { cache: "no-store" });
  });

  it("creates a post with a JSON message payload", async () => {
    const post = { id: "post-1", message: "Hello", created_at: "2026-07-31T10:00:00Z" };
    fetchMock.mockResolvedValueOnce(jsonResponse(post, 201));

    await expect(createPost({ message: "Hello" })).resolves.toEqual(post);
    expect(fetchMock).toHaveBeenCalledWith("/api/posts", {
      body: JSON.stringify({ message: "Hello" }),
      headers: { "Content-Type": "application/json" },
      method: "POST"
    });
  });

  it("throws a safe error when creation fails", async () => {
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 500 }));

    await expect(createPost({ message: "Hello" })).rejects.toThrow("Unable to create post");
  });
});
