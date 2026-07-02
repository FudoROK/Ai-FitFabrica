"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { MaterialIcon } from "@/components/site/material-icon";
import { SiteButton } from "@/components/site/site-button";
import { WebApiClient } from "@/lib/api/client";

type FormState = {
  company: string;
  email: string;
  name: string;
  size: string;
  tools: string[];
  type: string;
};

const initialState: FormState = {
  company: "",
  email: "",
  name: "",
  size: "< 100",
  tools: [],
  type: "Ритейлер одежды"
};

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
}

const toolOptions = [
  "Виртуальная примерка",
  "Карточки товара и контент",
  "AI-стилист и рекомендации"
];

export function ContactForm() {
  const [form, setForm] = useState<FormState>(initialState);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

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
        message: [
          `Размер каталога: ${form.size}`,
          `Тип бизнеса: ${form.type}`,
          form.tools.length ? `Интересующие сценарии: ${form.tools.join(", ")}` : undefined
        ]
          .filter(Boolean)
          .join("\n"),
        name: form.name.trim()
      });

      if (!response.ok) {
        setError("Сервер не принял заявку. Проверьте данные и повторите отправку.");
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
    <form className="site-card rounded-[2.75rem] p-14" onSubmit={handleSubmit}>
      <h2 className="public-form-title">Запросить демонстрацию</h2>

      <div className="mt-10 grid gap-8 md:grid-cols-2">
        <label className="public-form-label grid gap-3">
          <span>Имя</span>
          <input className="site-input" onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} value={form.name} />
        </label>
        <label className="public-form-label grid gap-3">
          <span>Рабочий email</span>
          <input className="site-input" onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))} type="email" value={form.email} />
        </label>
        <label className="public-form-label grid gap-3">
          <span>Название бренда / компании</span>
          <input className="site-input" onChange={(event) => setForm((current) => ({ ...current, company: event.target.value }))} value={form.company} />
        </label>
        <label className="public-form-label grid gap-3">
          <span>Размер каталога (SKU)</span>
          <select className="site-select appearance-none" onChange={(event) => setForm((current) => ({ ...current, size: event.target.value }))} value={form.size}>
            <option>&lt; 100</option>
            <option>100 - 500</option>
            <option>500 - 2000</option>
            <option>2000+</option>
          </select>
        </label>
      </div>

      <label className="public-form-label mt-8 grid gap-3">
        <span>Тип бизнеса</span>
        <select className="site-select appearance-none" onChange={(event) => setForm((current) => ({ ...current, type: event.target.value }))} value={form.type}>
          <option>Ритейлер одежды</option>
          <option>Маркетплейс</option>
          <option>Производитель</option>
          <option>Контент-студия</option>
        </select>
      </label>

      <div className="mt-10">
        <p className="public-form-label">Интересующие сценарии</p>
        <div className="mt-5 grid gap-4">
          {toolOptions.map((tool) => {
            const checked = form.tools.includes(tool);

            return (
              <label className="public-body flex items-center gap-4" key={tool}>
                <input
                  checked={checked}
                  className="h-7 w-7 accent-[var(--ai)]"
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      tools: event.target.checked
                        ? [...current.tools, tool]
                        : current.tools.filter((item) => item !== tool)
                    }))
                  }
                  type="checkbox"
                />
                <span>{tool}</span>
              </label>
            );
          })}
        </div>
      </div>

      {error ? <p className="mt-6 rounded-2xl bg-[#fce8e6] px-5 py-4 text-sm font-medium text-[var(--error)]">{error}</p> : null}
      {success ? <p className="mt-6 rounded-2xl bg-[var(--success-soft)] px-5 py-4 text-sm font-medium text-[var(--success)]">{success}</p> : null}

      <SiteButton className="mt-10 w-full" icon="arrow_forward" type="submit" variant="violet" disabled={isSubmitting}>
        {isSubmitting ? "Отправляем заявку" : "Запросить демо"}
      </SiteButton>

      <p className="mt-10 text-center text-[0.95rem] font-semibold tracking-[0.08em] text-[var(--text-muted)]">
        Отправляя форму, вы соглашаетесь на обработку контактных данных для связи по демонстрации.
      </p>

      <div className="mt-8 flex gap-4 text-[var(--text-secondary)]">
        <MaterialIcon className="ui-label-strong" name="mail" />
        <span>hello@fitfabrica.ai</span>
      </div>
    </form>
  );
}
