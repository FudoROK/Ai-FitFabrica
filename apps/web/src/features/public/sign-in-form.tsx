"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { MaterialIcon } from "@/components/site/material-icon";
import { SiteButton } from "@/components/site/site-button";
import { WebApiClient } from "@/lib/api/client";

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
}

export function SignInForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!email.trim() || !password.trim()) {
      setError("Введите email и пароль.");
      return;
    }

    const baseUrl = getApiBaseUrl();

    if (!baseUrl) {
      setError("Не настроен адрес backend для входа.");
      return;
    }

    setIsSubmitting(true);

    try {
      const client = new WebApiClient(baseUrl);
      const response = await client.signIn({ email: email.trim(), password });

      if (!response.ok) {
        setError("Вход отклонен. Проверьте email и пароль.");
        return;
      }

      setSuccess("Вход подтвержден. Можно продолжать работу в workspace.");
    } catch {
      setError("Не удалось выполнить вход. Проверьте подключение к backend.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="site-card mx-auto mt-40 w-full max-w-[550px] rounded-[3rem] p-10" onSubmit={handleSubmit}>
      <div className="grid grid-cols-2 border-b border-[var(--border)] text-center text-[2rem] font-medium">
        <div className="border-b-2 border-black pb-4">Войти</div>
        <div className="pb-4 text-[var(--text-secondary)]">Регистрация</div>
      </div>

      <button className="site-pill-button mt-8 w-full" type="button">
        <span className="ui-label-strong">G</span>
        <span>Продолжить с Google</span>
      </button>

      <div className="my-8 flex items-center gap-4 text-[var(--text-muted)]">
        <div className="h-px flex-1 bg-[var(--border)]" />
        <span className="eyebrow">или</span>
        <div className="h-px flex-1 bg-[var(--border)]" />
      </div>

      <label className="public-form-label grid gap-3">
        <span>Email</span>
        <input className="site-input" onChange={(event) => setEmail(event.target.value)} type="email" value={email} />
      </label>

      <div className="mt-6 flex items-center justify-between">
        <span className="public-form-label">Пароль</span>
        <button className="site-pill-button site-pill-button--compact" type="button">
          Забыли пароль?
        </button>
      </div>

      <label className="relative mt-3 block">
        <input className="site-input pr-14" onChange={(event) => setPassword(event.target.value)} type="password" value={password} />
        <span className="absolute right-5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]">
          <MaterialIcon name="visibility" />
        </span>
      </label>

      {error ? <p className="mt-6 rounded-2xl bg-[#fce8e6] px-5 py-4 text-sm font-medium text-[var(--error)]">{error}</p> : null}
      {success ? <p className="mt-6 rounded-2xl bg-[var(--success-soft)] px-5 py-4 text-sm font-medium text-[var(--success)]">{success}</p> : null}

      <SiteButton className="mt-8 w-full" type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Проверяем доступ" : "Войти"}
      </SiteButton>
    </form>
  );
}
