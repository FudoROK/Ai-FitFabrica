"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { FormField } from "@/components/ui/form-field";
import { WebApiClient } from "@/lib/api/client";

type SignInState = {
  email: string;
  password: string;
};

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
}

export function SignInForm() {
  const [form, setForm] = useState<SignInState>({ email: "", password: "" });
  const [error, setError] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState<string>("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!form.email.trim() || !form.password.trim()) {
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
      const response = await client.signIn({
        email: form.email.trim(),
        password: form.password
      });

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
    <form className="surface-card auth-shell" onSubmit={handleSubmit}>
      <div className="form-shell-header">
        <p className="eyebrow">Доступ к workspace</p>
        <h1 className="section-title">Вход в рабочее пространство</h1>
        <p className="section-copy">
          Войдите по email или используйте корпоративную авторизацию, когда backend
          будет подключен к вашему identity provider.
        </p>
      </div>
      <div className="form-grid">
        <FormField
          id="sign-in-email"
          label="Email"
          onChange={(value) => setForm((current) => ({ ...current, email: value }))}
          placeholder="name@company.com"
          required
          type="email"
          value={form.email}
        />
        <FormField
          id="sign-in-password"
          label="Пароль"
          onChange={(value) => setForm((current) => ({ ...current, password: value }))}
          placeholder="Введите пароль"
          required
          type="password"
          value={form.password}
        />
      </div>
      <div className="auth-options">
        <button className="button button-primary" disabled={isSubmitting} type="submit">
          {isSubmitting ? "Проверяем доступ" : "Войти по email"}
        </button>
        <button className="button button-secondary" disabled type="button">
          Продолжить с Google
        </button>
      </div>
      {error ? <p className="form-error-banner">{error}</p> : null}
      {success ? <p className="form-success-banner">{success}</p> : null}
      <div className="surface-subcard auth-note">
        <h2>Что подключить позже</h2>
        <p>Google Sign-In, protected routes и redirect после успешного входа подключаются на backend-first контракте.</p>
      </div>
    </form>
  );
}
