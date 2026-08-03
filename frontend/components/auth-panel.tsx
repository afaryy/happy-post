"use client";

import { FormEvent, useState } from "react";

type AuthPanelProps = {
  error: string | null;
  isSubmitting: boolean;
  onSignin: (email: string, password: string) => Promise<void>;
  onSignup: (email: string, password: string) => Promise<void>;
};

export function AuthPanel({ error, isSubmitting, onSignin, onSignup }: AuthPanelProps) {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const canSubmit = email.trim().length > 0 && password.length >= 10 && !isSubmitting;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }
    if (mode === "signin") {
      await onSignin(email.trim(), password);
    } else {
      await onSignup(email.trim(), password);
    }
  }

  return (
    <main>
      <div className="auth-shell">
        <div className="moon-glow" aria-hidden="true" />
        <section className="card auth-card" aria-labelledby="auth-title">
          <p className="eyebrow">Your private bedtime space</p>
          <h1 id="auth-title">
            {mode === "signin" ? "Sign in to your Happy Post" : "Create your Happy Post"}
          </h1>
          <p className="intro">
            Keep a gentle history of your small happy things, just for you.
          </p>

          <form className="auth-form" onSubmit={handleSubmit}>
            <label className="happy-field">
              <span>Email</span>
              <input
                autoComplete="email"
                onChange={(event) => setEmail(event.target.value)}
                type="email"
                value={email}
              />
            </label>
            <label className="happy-field">
              <span>Password</span>
              <input
                autoComplete={mode === "signin" ? "current-password" : "new-password"}
                minLength={10}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                value={password}
              />
            </label>

            {error ? <p role="alert">{error}</p> : null}

            <button className="primary-button" disabled={!canSubmit} type="submit">
              {isSubmitting ? "Warming up…" : mode === "signin" ? "Sign in" : "Sign up"}
            </button>
          </form>

          <button
            className="link-button"
            onClick={() => setMode(mode === "signin" ? "signup" : "signin")}
            type="button"
          >
            {mode === "signin"
              ? "New here? Create a gentle space"
              : "Already have a space? Sign in"}
          </button>
        </section>
      </div>
    </main>
  );
}
