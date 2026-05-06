"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { FormField } from "@/components/ui/form-field";
import { FormTextarea } from "@/components/ui/form-textarea";
import { WebApiClient } from "@/lib/api/client";

type FormState = {
  company: string;
  email: string;
  message: string;
  name: string;
};

const initialState: FormState = {
  company: "",
  email: "",
  message: "",
  name: ""
};

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
}

export function ContactForm() {
  const [form, setForm] = useState<FormState>(initialState);
  const [error, setError] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState<string>("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!form.name.trim() || !form.email.trim()) {
      setError("Укажите имя и рабочий email.");
      return;
    }

    const baseUrl = getApiBaseUrl();

    if (!baseUrl) {
      setError("Не настроен адрес backend для отправки заявки.");
      return;
    }

    setIsSubmitting(true);

    try {
      const client = new WebApiClient(baseUrl);
      const response = await client.requestDemo({
        company: form.company.trim() || undefined,
        email: form.email.trim(),
        message: form.message.trim() || undefined,
        name: form.name.trim()
      });

      if (!response.ok) {
        setError("Сервер не принял заявку. Проверьте данные и повторите.");
        return;
      }

      setForm(initialState);
      setSuccess("Заявка отправлена. Команда FitFabrica свяжется с вами после проверки.");
    } catch {
      setError("Не удалось отправить заявку. Проверьте подключение к backend.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="surface-card form-shell" onSubmit={handleSubmit}>
      <div className="form-shell-header">
        <p className="eyebrow">Запрос демо</p>
        <h2 className="section-title">Запросить демонстрацию</h2>
        <p className="section-copy">
          Оставьте контакты и кратко опишите каталог, ассортимент или задачу. Мы
          вернемся с подходящим сценарием запуска.
        </p>
      </div>
      <div className="form-grid">
        <FormField
          id="contact-name"
          label="Имя"
          onChange={(value) => setForm((current) => ({ ...current, name: value }))}
          placeholder="Анна Соколова"
          required
          value={form.name}
        />
        <FormField
          id="contact-email"
          label="Рабочий email"
          onChange={(value) => setForm((current) => ({ ...current, email: value }))}
          placeholder="brand@company.com"
          required
          type="email"
          value={form.email}
        />
        <FormField
          helper="Опционально"
          id="contact-company"
          label="Компания"
          onChange={(value) => setForm((current) => ({ ...current, company: value }))}
          placeholder="FitFabrica Retail"
          value={form.company}
        />
        <div className="surface-subcard form-note">
          <h3>Что будет дальше</h3>
          <p>Разберем ваш каталог, оценим сценарии генерации и предложим дорожную карту внедрения.</p>
        </div>
        <FormTextarea
          helper="Можно описать ассортимент, объем каталога, канал продаж или сроки."
          id="contact-message"
          label="Задача"
          onChange={(value) => setForm((current) => ({ ...current, message: value }))}
          placeholder="Нужно ускорить подготовку карточек товара и снизить стоимость контента."
          rows={5}
          value={form.message}
        />
      </div>
      {error ? <p className="form-error-banner">{error}</p> : null}
      {success ? <p className="form-success-banner">{success}</p> : null}
      <div className="form-actions">
        <button className="button button-primary" disabled={isSubmitting} type="submit">
          {isSubmitting ? "Отправляем заявку" : "Отправить заявку"}
        </button>
        <p className="form-helper">Нажимая кнопку, вы соглашаетесь на обработку персональных данных.</p>
      </div>
    </form>
  );
}
