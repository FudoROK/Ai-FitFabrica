"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useState } from "react";
import Image from "next/image";
import { SiteButton } from "@/components/site/site-button";
import { WorkspaceShellState } from "@/features/workspace/workspace-shell-state";
import { useWorkspaceRuntime } from "@/features/workspace/workspace-runtime";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";
import type { ProductCardJobResponse, ProductCardResultResponse } from "@/lib/api/contracts";

const acceptedTypes = ["image/jpeg", "image/png", "image/webp"] as const;
const maxFileSize = 10 * 1024 * 1024;

type SelectedImage = {
  error: string;
  file: File | null;
  previewUrl: string;
};

const emptyImage: SelectedImage = { error: "", file: null, previewUrl: "" };

function validateImage(file: File | null): string {
  if (!file) return "Добавьте фото товара.";
  if (!acceptedTypes.includes(file.type as (typeof acceptedTypes)[number])) return "Разрешены JPEG, PNG и WebP.";
  if (file.size === 0) return "Файл пустой.";
  if (file.size > maxFileSize) return "Максимальный размер файла — 10 МБ.";
  return "";
}

async function fileToBase64(file: File): Promise<string> {
  const bytes = new Uint8Array(await file.arrayBuffer());
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return window.btoa(binary);
}

export function ProductCardWorkflow() {
  const { bootstrap, error: bootstrapError, hasCapability: workspaceHasCapability, isLoading, refresh } = useWorkspaceRuntime();
  const [image, setImage] = useState<SelectedImage>(emptyImage);
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("");
  const [targetChannel, setTargetChannel] = useState("");
  const [brandTone, setBrandTone] = useState("");
  const [job, setJob] = useState<ProductCardJobResponse | null>(null);
  const [result, setResult] = useState<ProductCardResultResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const hasProductCardCapability = workspaceHasCapability("product_card_create");
  const requiredCredits = bootstrap?.workflow_costs.product_card ?? 0;
  const hasCredits = Boolean(bootstrap && (!bootstrap.credits.billing_enabled || bootstrap.credits.balance >= requiredCredits));
  const hasRequiredData = Boolean(image.file && !image.error && title.trim() && category && targetChannel && brandTone);
  const canSubmit = hasRequiredData && hasProductCardCapability && hasCredits && !isSubmitting && !job;
  const disabledReason = job
    ? "Задача уже создана."
    : !hasProductCardCapability
      ? "Создание карточек недоступно для этого workspace."
      : !hasCredits
        ? `Для запуска требуется ${requiredCredits} кредитов.`
        : !hasRequiredData
          ? "Добавьте фото, название, категорию, канал и формат карточки."
          : "";

  useEffect(() => () => {
    if (image.previewUrl) URL.revokeObjectURL(image.previewUrl);
  }, [image.previewUrl]);

  useEffect(() => {
    if (!job || job.status === "completed" || job.status === "failed") return;
    let active = true;
    const timer = window.setTimeout(async () => {
      try {
        const client = new WebApiClient(getApiBaseUrl());
        const nextJob = await client.getProductCardJob(job.job_id);
        if (!active) return;
        setJob(nextJob);
        if (nextJob.status === "completed") {
          setResult(await client.getProductCardResult(nextJob.job_id));
          await refresh();
        }
      } catch (requestError) {
        if (active) setError(requestError instanceof Error ? requestError.message : "Не удалось обновить статус.");
      }
    }, 2000);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [job, refresh]);

  function handleImageChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    const nextError = validateImage(file);
    if (image.previewUrl) URL.revokeObjectURL(image.previewUrl);
    setImage({
      error: nextError,
      file: nextError ? null : file,
      previewUrl: nextError || !file ? "" : URL.createObjectURL(file),
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!canSubmit || !image.file) return;
    setIsSubmitting(true);
    try {
      const client = new WebApiClient(getApiBaseUrl());
      const created = await client.createProductCardJob({
        title_hint: title.trim(),
        category,
        target_channel: targetChannel,
        brand_tone: brandTone,
        source_files: [{
          filename: image.file.name,
          content_type: image.file.type,
          payload_base64: await fileToBase64(image.file),
        }],
      });
      setJob(created);
      if (created.status === "completed") {
        setResult(await client.getProductCardResult(created.job_id));
        await refresh();
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось создать карточку товара.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!bootstrap) {
    return <WorkspaceShellState error={bootstrapError} hasBootstrap={Boolean(bootstrap)} isLoading={isLoading} onRetry={refresh} />;
  }

  return (
    <form className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]" onSubmit={handleSubmit}>
      <section className="site-card p-7 lg:p-8">
        <h2 className="workspace-section-title">Новая карточка товара</h2>
        <label className="public-form-label mt-6 grid gap-3">
          <span>Фото товара</span>
          <input accept="image/jpeg,image/png,image/webp" disabled={isSubmitting || Boolean(job)} onChange={handleImageChange} type="file" />
        </label>
        {image.previewUrl ? (
          <div className="relative mt-4 aspect-[4/3] overflow-hidden rounded-[1.5rem] bg-[var(--surface-alt)]">
            <Image alt="Предпросмотр товара" fill className="object-contain" src={image.previewUrl} unoptimized />
          </div>
        ) : null}
        {image.error ? <p className="workspace-meta mt-3 text-[var(--error)]">{image.error}</p> : null}
        <div className="mt-6 grid gap-5">
          <label className="public-form-label grid gap-3"><span>Название</span><input className="site-input" disabled={isSubmitting || Boolean(job)} onChange={(event) => setTitle(event.target.value)} value={title} /></label>
          <label className="public-form-label grid gap-3"><span>Категория</span><select className="site-input" disabled={isSubmitting || Boolean(job)} name="category" onChange={(event) => setCategory(event.target.value)} value={category}><option value="">Выберите категорию</option><option value="dress">Платье</option><option value="shirt">Рубашка</option><option value="outerwear">Верхняя одежда</option><option value="footwear">Обувь</option><option value="accessory">Аксессуар</option></select></label>
          <label className="public-form-label grid gap-3"><span>Канал карточки</span><select className="site-input" disabled={isSubmitting || Boolean(job)} name="target_channel" onChange={(event) => setTargetChannel(event.target.value)} value={targetChannel}><option value="">Выберите канал</option><option value="wildberries">Wildberries</option><option value="ozon">Ozon</option><option value="instagram">Instagram</option><option value="shopify">Shopify</option></select></label>
          <label className="public-form-label grid gap-3"><span>Формат и тон</span><select className="site-input" disabled={isSubmitting || Boolean(job)} name="brand_tone" onChange={(event) => setBrandTone(event.target.value)} value={brandTone}><option value="">Выберите формат</option><option value="marketplace concise">Marketplace: кратко</option><option value="premium editorial">Premium editorial</option><option value="social commerce">Social commerce</option></select></label>
        </div>
        {error ? <p className="mt-5 rounded-2xl bg-[#fce8e6] px-5 py-4 text-sm font-medium text-[var(--error)]">{error}</p> : null}
        <SiteButton className="mt-7 w-full" disabled={!canSubmit} type="submit" variant="violet">
          {isSubmitting ? "Создаём карточку..." : `Создать карточку · ${requiredCredits} кредитов`}
        </SiteButton>
        {disabledReason ? <p className="workspace-meta mt-3">{disabledReason}</p> : null}
        {!hasProductCardCapability ? <p className="workspace-meta mt-3 text-[var(--error)]">Capability product_card_create недоступна.</p> : null}
        {!hasCredits ? <p className="workspace-meta mt-3 text-[var(--error)]">Недостаточно кредитов для запуска.</p> : null}
      </section>

      <section className="site-card p-7 lg:p-8">
        <p className="eyebrow">Backend workflow</p>
        <h2 className="workspace-section-title mt-4">{job ? `Задача ${job.job_id}` : "Ожидание запуска"}</h2>
        <p className="workspace-body mt-4">{job ? `Статус: ${job.status}` : "После отправки здесь появятся реальный job status и результат."}</p>
        {result ? (
          <div className="mt-6 grid gap-4">
            <h3 className="workspace-card-title">{result.title}</h3>
            <p className="workspace-body">{result.description}</p>
            <ul className="grid gap-2">{result.bullet_points.map((item) => <li className="workspace-meta" key={item}>• {item}</li>)}</ul>
          </div>
        ) : null}
      </section>
    </form>
  );
}
