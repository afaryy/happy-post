"use client";

import { useEffect, useState } from "react";

import { PostForm } from "@/components/post-form";
import { PostList } from "@/components/post-list";
import { createPost, listPosts } from "@/lib/api";
import type { Post } from "@/lib/types";

export default function Page() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const [submitError, setSubmitError] = useState(false);

  useEffect(() => {
    let active = true;

    void listPosts()
      .then((loadedPosts) => {
        if (active) {
          setPosts(loadedPosts);
        }
      })
      .catch(() => {
        if (active) {
          setLoadError(true);
        }
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  async function handleCreate(message: string) {
    setIsSubmitting(true);
    setSubmitError(false);

    try {
      const post = await createPost({ message });
      setPosts((currentPosts) => [post, ...currentPosts]);
    } catch {
      setSubmitError(true);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main>
      <h1>Happy Post</h1>
      <PostForm isSubmitting={isSubmitting} onSubmit={handleCreate} />
      {submitError ? <p role="alert">Unable to create post.</p> : null}
      {isLoading ? <p>Loading posts…</p> : null}
      {loadError ? <p role="alert">Unable to load posts.</p> : null}
      {!isLoading && !loadError ? <PostList posts={posts} /> : null}
    </main>
  );
}
