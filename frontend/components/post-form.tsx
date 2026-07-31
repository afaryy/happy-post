"use client";

import { FormEvent, useState } from "react";

type PostFormProps = {
  isSubmitting: boolean;
  onSubmit: (message: string) => Promise<void>;
};

export function PostForm({ isSubmitting, onSubmit }: PostFormProps) {
  const [message, setMessage] = useState("");
  const canSubmit = message.trim().length > 0 && !isSubmitting;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }

    await onSubmit(message.trim());
    setMessage("");
  }

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="message">Message</label>
      <input
        id="message"
        name="message"
        onChange={(event) => setMessage(event.target.value)}
        value={message}
      />
      <button disabled={!canSubmit} type="submit">
        {isSubmitting ? "Posting…" : "Post"}
      </button>
    </form>
  );
}
