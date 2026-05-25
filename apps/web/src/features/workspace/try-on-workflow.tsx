"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { SiteButton } from "@/components/site/site-button";
import { WebApiClient } from "@/lib/api/client";
import type { TryOnJobStatusResponse, TryOnStatusEvent } from "@/lib/api/contracts";

type UploadRole = "human_photo" | "garment_photo";
type SelectedImage = { error: string; file: File | null; previewUrl: string };
type WorkflowState = "idle" | "submitting" | "status_loaded" | "completed" | "error";
type UploadCardProps = {
  description: string;
  image: SelectedImage;
  label: string;
  name: UploadRole;
  onChange: (role: UploadRole, file: File | null) => void;
};

const acceptedImageTypes = ["image/jpeg", "image/png", "image/webp"] as const;
const acceptedImageTypesLabel = "JPEG, PNG, WebP до 10MB";
const maxFileSizeBytes = 10 * 1024 * 1024;
const emptyImage: SelectedImage = { error: "", file: null, previewUrl: "" };

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
}

function validateImageFile(file: File | null): string {
  if (!file) {
    return "Выберите файл изображения.";
  }

  if (file.size === 0) {
    return "Файл пустой. Выберите другое изображение.";
  }

  if (!acceptedImageTypes.includes(file.type as (typeof acceptedImageTypes)[number])) {
    return "Поддерживаются только JPEG, PNG или WebP.";
  }

  if (file.size > maxFileSizeBytes) {
    return "Максимальный размер файла - 10MB.";
  }

  return "";
}

function formatStatusTime(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("ru-RU", { day: "2-digit", hour: "2-digit", minute: "2-digit", month: "2-digit" });
}

function UploadCard({ description, image, label, name, onChange }: UploadCardProps) {
  return (
    <label className="upload-card flex w-full max-w-[220px] cursor-pointer flex-col items-center justify-center border-2 border-dashed border-[#d8c3a5] bg-[var(--surface)] p-4 text-center transition hover:bg-[var(--surface-alt)]">
      <input
        accept="image/jpeg,image/png,image/webp"
        className="sr-only"
        name={name}
        onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(name, event.target.files?.[0] ?? null)}
        type="file"
      />
      {image.previewUrl ? (
        <span className="relative block h-[190px] w-full overflow-hidden rounded-[1.5rem]">
          <Image alt={label} className="object-cover" fill src={image.previewUrl} unoptimized />
        </span>
      ) : (
        <div className="flex h-[190px] w-full items-center justify-center rounded-[1.5rem] bg-[var(--ai-soft)] text-[2.5rem] text-[var(--ai)]">
          +
        </div>
      )}
      <h2 className="upload-card-title mt-5 font-semibold">{label}</h2>
      <p className="upload-card-description mt-2 text-[var(--text-secondary)]">{description}</p>
      {image.file ? <p className="mt-2 max-w-full truncate text-[0.78rem] font-medium text-[var(--text-muted)]">{image.file.name}</p> : null}
      {image.error ? <p className="mt-3 text-[0.78rem] font-semibold text-[var(--error)]">{image.error}</p> : null}
    </label>
  );
}

function StatusHistory({ items }: { items: TryOnStatusEvent[] }) {
  if (!items.length) {
    return (
      <div className="rounded-[1.2rem] bg-[var(--background)] p-4">
        <strong className="block text-[0.95rem]">Ожидание запуска</strong>
        <p className="mt-1 text-[0.85rem] leading-6 text-[var(--text-secondary)]">
          После отправки backend вернет историю статусов job.
        </p>
      </div>
    );
  }

  return (
    <>
      {items.map((item) => (
        <div className="rounded-[1.2rem] bg-[var(--background)] p-4" key={`${item.status}-${item.occurred_at}`}>
          <div className="flex items-start justify-between gap-3">
            <strong className="block text-[0.95rem]">{item.stage}</strong>
            <span className="rounded-full bg-[var(--ai-soft)] px-2 py-1 text-[0.7rem] font-semibold text-[var(--ai)]">
              {item.status}
            </span>
          </div>
          <p className="mt-2 text-[0.85rem] leading-6 text-[var(--text-secondary)]">{item.message}</p>
          <p className="mt-2 text-[0.72rem] font-medium text-[var(--text-muted)]">{formatStatusTime(item.occurred_at)}</p>
        </div>
      ))}
    </>
  );
}

export function TryOnWorkflow() {
  const router = useRouter();
  const [humanPhoto, setHumanPhoto] = useState<SelectedImage>(emptyImage);
  const [garmentPhoto, setGarmentPhoto] = useState<SelectedImage>(emptyImage);
  const [workflowState, setWorkflowState] = useState<WorkflowState>("idle");
  const [status, setStatus] = useState<TryOnJobStatusResponse | null>(null);
  const [createdJobId, setCreatedJobId] = useState("");
  const [error, setError] = useState("");
  const isSubmitting = workflowState === "submitting";
  const canSubmit = Boolean(humanPhoto.file && garmentPhoto.file) && !humanPhoto.error && !garmentPhoto.error && !isSubmitting;

  useEffect(() => {
    return () => {
      if (humanPhoto.previewUrl) {
        URL.revokeObjectURL(humanPhoto.previewUrl);
      }

      if (garmentPhoto.previewUrl) {
        URL.revokeObjectURL(garmentPhoto.previewUrl);
      }
    };
  }, [humanPhoto.previewUrl, garmentPhoto.previewUrl]);

  function updateImage(role: UploadRole, file: File | null) {
    const errorMessage = validateImageFile(file);
    const nextImage: SelectedImage = {
      error: errorMessage,
      file: errorMessage ? null : file,
      previewUrl: errorMessage || !file ? "" : URL.createObjectURL(file)
    };

    if (role === "human_photo") {
      if (humanPhoto.previewUrl) {
        URL.revokeObjectURL(humanPhoto.previewUrl);
      }

      setHumanPhoto(nextImage);
      return;
    }

    if (garmentPhoto.previewUrl) {
      URL.revokeObjectURL(garmentPhoto.previewUrl);
    }

    setGarmentPhoto(nextImage);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setStatus(null);

    const humanError = validateImageFile(humanPhoto.file);
    const garmentError = validateImageFile(garmentPhoto.file);

    if (humanError || garmentError) {
      setHumanPhoto((current) => ({ ...current, error: humanError }));
      setGarmentPhoto((current) => ({ ...current, error: garmentError }));
      setWorkflowState("error");
      return;
    }

    const baseUrl = getApiBaseUrl();

    if (!baseUrl) {
      setError("Не настроен NEXT_PUBLIC_API_BASE_URL. Укажите backend base URL для создания примерки.");
      setWorkflowState("error");
      return;
    }

    if (!humanPhoto.file || !garmentPhoto.file) {
      setError("Выберите фото человека и фото одежды.");
      setWorkflowState("error");
      return;
    }

    setWorkflowState("submitting");

    try {
      const formData = new FormData();
      formData.append("human_photo", humanPhoto.file);
      formData.append("garment_photo", garmentPhoto.file);

      const client = new WebApiClient(baseUrl);
      const created = await client.createTryOnJob(formData);
      setCreatedJobId(created.job_id);

      const currentStatus = await client.getJobStatus(created.job_id);
      setStatus(currentStatus);

      if (currentStatus.status === "completed") {
        setWorkflowState("completed");
        router.push(`/workspace/try-on/result?job_id=${encodeURIComponent(created.job_id)}`);
        return;
      }

      setWorkflowState("status_loaded");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось создать job примерки.");
      setWorkflowState("error");
    }
  }

  return (
    <main className="flex h-full min-w-0 flex-col overflow-hidden bg-[var(--background)]">
      <div className="border-b border-[var(--border)] bg-[var(--surface)] px-5 py-4 lg:px-6">
        <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <h1 className="workspace-title font-[family-name:var(--font-manrope)]">Новая примерка</h1>
            <p className="workspace-subtitle mt-2 max-w-[760px] text-[var(--text-secondary)]">
              Загрузите фото человека и фото одежды. Frontend отправит файлы на backend и покажет текущий статус job.
            </p>
          </div>
          <Link className="site-pill-button site-pill-button--compact" href="/workspace/chat">
            Вернуться в общий чат
          </Link>
        </div>
      </div>

      <section className="min-h-0 flex-1 overflow-hidden p-5 lg:p-6">
        <form className="tryon-layout grid h-full min-w-0 gap-5 overflow-hidden" onSubmit={handleSubmit}>
          <div className="min-h-0 overflow-y-auto overflow-x-hidden">
            <div className="grid gap-5">
              <UploadCard description={acceptedImageTypesLabel} image={humanPhoto} label="Фото человека" name="human_photo" onChange={updateImage} />
              <UploadCard description={acceptedImageTypesLabel} image={garmentPhoto} label="Фото одежды" name="garment_photo" onChange={updateImage} />
            </div>
          </div>

          <div className="workspace-main min-h-0 min-w-0 overflow-y-auto overflow-x-hidden">
            <div className="result-card site-card flex min-w-0 items-center justify-center p-8 lg:p-10">
              <div className="text-center">
                <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-full bg-[var(--ai-soft)] text-[2.5rem] text-[var(--ai)]">
                  {isSubmitting ? "..." : "AI"}
                </div>
                <h2 className="result-title mt-6 font-[family-name:var(--font-manrope)] font-bold tracking-[-0.04em]">
                  {workflowState === "completed" ? "Job завершен" : "Подготовка примерки"}
                </h2>
                <p className="result-description mx-auto mt-4 max-w-[620px] text-[var(--text-secondary)]">
                  {createdJobId
                    ? `Job ${createdJobId} создан. Результат будет открыт после статуса completed.`
                    : "Выберите два изображения и отправьте их на backend. Генерация, качество и сохранение остаются на стороне backend."}
                </p>
                {workflowState === "status_loaded" && status ? (
                  <p className="mt-5 rounded-2xl bg-[var(--success-soft)] px-5 py-4 text-sm font-medium text-[var(--success)]">
                    Статус получен: {status.status}. Если backend еще работает, продолжайте отслеживание на result page.
                  </p>
                ) : null}
                {error ? <p className="mt-5 rounded-2xl bg-[#fce8e6] px-5 py-4 text-sm font-medium text-[var(--error)]">{error}</p> : null}
              </div>
            </div>
          </div>

          <aside className="workspace-status min-h-0 overflow-y-auto overflow-x-hidden pr-1">
            <div className="site-card flex min-h-0 flex-col justify-between p-6">
              <div>
                <h2 className="text-[1.35rem] font-semibold">Статус backend</h2>
                <div className="mt-6 grid gap-4">
                  <StatusHistory items={status?.status_history ?? []} />
                </div>
              </div>
              <div className="mt-6">
                <div className="mb-4 flex items-center justify-between gap-4 text-[0.95rem]">
                  <span className="text-[var(--text-secondary)]">Sandbox charge:</span>
                  <strong>0 кредитов</strong>
                </div>
                <SiteButton className="w-full" disabled={!canSubmit} type="submit" variant="violet">
                  {isSubmitting ? "Создаем job..." : "Создать примерку"}
                </SiteButton>
                <p className="mt-3 text-center text-[0.82rem] font-medium text-[var(--text-muted)]">
                  {canSubmit ? "Файлы готовы к отправке" : "Загрузите оба изображения для начала"}
                </p>
              </div>
            </div>
          </aside>
        </form>
      </section>
    </main>
  );
}
