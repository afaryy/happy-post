import type { CreatePostInput, Post } from "@/lib/types";

async function requireSuccess(response: Response, message: string): Promise<Response> {
  if (!response.ok) {
    throw new Error(message);
  }
  return response;
}

export async function listPosts(): Promise<Post[]> {
  const response = await fetch("/api/posts", { cache: "no-store" });
  return requireSuccess(response, "Unable to load posts").then((result) => result.json());
}

export async function createPost(input: CreatePostInput): Promise<Post> {
  const response = await fetch("/api/posts", {
    body: JSON.stringify(input),
    headers: { "Content-Type": "application/json" },
    method: "POST"
  });
  return requireSuccess(response, "Unable to create post").then((result) => result.json());
}
