"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { SiteButton } from "@/components/site/site-button";
import { WebApiClient } from "@/lib/api/client";
import type { TryOnJobStatusResponse, TryOnStatusEvent } from "@/lib/api/contracts";

type UploadRole = "human_photo" | "garment_photo";
type SelectedImage = { error: string; file: File | null; previewUrl: string };
type WorkflowState = "idle" | "submitting" | "status_loaded" | "completed" | "error";
type UploadCardProps = {
  description: string; disabled: boolean; image: SelectedImage; label: string; name: UploadRole;
  onChange: (role: UploadRole, file: File | null) => void;
};

const acceptedImageTypes = ["image/jpeg", "image/png", "image/webp"] as const;
const acceptedImageTypesLabel = "JPEG, PNG РёР»Рё WebP, РґРѕ 10 РњР‘";
const maxFileSizeBytes = 10 * 1024 * 1024;
const emptyImage: SelectedImage = { error: "", file: null, previewUrl: "" };

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
}

function validateImageFile(file: File | null): string {
  if (!file) {
    return "Р’С‹Р±РµСЂРёС‚Рµ С„Р°Р№Р» РёР·РѕР±СЂР°Р¶РµРЅРёСЏ.";
  }
  if (file.size === 0) {
    return "Р¤Р°Р№Р» РїСѓСЃС‚РѕР№. Р’С‹Р±РµСЂРёС‚Рµ РґСЂСѓРіРѕРµ РёР·РѕР±СЂР°Р¶РµРЅРёРµ.";
  }
  if (!acceptedImageTypes.includes(file.type as (typeof acceptedImageTypes)[number])) {
    return "РџРѕРґРґРµСЂР¶РёРІР°СЋС‚СЃСЏ С‚РѕР»СЊРєРѕ JPEG, PNG РёР»Рё WebP.";
  }
  if (file.size > maxFileSizeBytes) {
    return "РњР°РєСЃРёРјР°Р»СЊРЅС‹Р№ СЂР°Р·РјРµСЂ С„Р°Р№Р»Р° - 10 РњР‘.";
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

function UploadCard({ description, disabled, image, label, name, onChange }: UploadCardProps) {
  return (
    <label
      aria-disabled={disabled}
      className={[
        "upload-card flex w-full max-w-[220px] flex-col items-center justify-center border-2 border-dashed border-[#d8c3a5] bg-[var(--surface)] p-4 text-center transition",
        disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer hover:bg-[var(--surface-alt)]"
      ].join(" ")}
    >
      <input
        accept="image/jpeg,image/png,image/webp"
        className="sr-only"
        disabled={disabled}
        name={name}
        onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(name, event.target.files?.[0] ?? null)}
        type="file"
      />
      {image.previewUrl ? (
        <span className="relative block h-[190px] w-full overflow-hidden rounded-[1.5rem]">
          <Image alt={label} className="object-cover" fill src={image.previewUrl} unoptimized />
        </span>
      ) : <div className="flex h-[190px] w-full items-center justify-center rounded-[1.5rem] bg-[var(--ai-soft)] text-[2.5rem] text-[var(--ai)]">+</div>}
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
        <strong className="block text-[0.95rem]">РћР¶РёРґР°РЅРёРµ Р·Р°РїСѓСЃРєР°</strong>
        <p className="mt-1 text-[0.85rem] leading-6 text-[var(--text-secondary)]">РџРѕСЃР»Рµ РѕС‚РїСЂР°РІРєРё Р±СЌРєРµРЅРґ РІРµСЂРЅРµС‚ РёСЃС‚РѕСЂРёСЋ СЃС‚Р°С‚СѓСЃРѕРІ Р·Р°РґР°С‡Рё.</p>
      </div>
    );
  }
  return (
    <>
      {items.map((item) => (
        <div className="rounded-[1.2rem] bg-[var(--background)] p-4" key={`${item.status}-${item.occurred_at}`}>
          <div className="flex items-start justify-between gap-3">
            <strong className="block text-[0.95rem]">{item.stage}</strong>
            <span className="rounded-full bg-[var(--ai-soft)] px-2 py-1 text-[0.7rem] font-semibold text-[var(--ai)]">{item.status}</span>
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
  const resultHref = createdJobId ? `/workspace/try-on/result?job_id=${encodeURIComponent(createdJobId)}` : "";
  const canSubmit = Boolean(humanPhoto.file && garmentPhoto.file) && !humanPhoto.error && !garmentPhoto.error && !isSubmitting && !createdJobId;

  useEffect(() => {
    return () => {
      if (humanPhoto.previewUrl) {
        URL.revokeObjectURL(humanPhoto.previewUrl);
      }
    };
  }, [humanPhoto.previewUrl]);

  useEffect(() => {
    return () => {
      if (garmentPhoto.previewUrl) {
        URL.revokeObjectURL(garmentPhoto.previewUrl);
      }
    };
  }, [garmentPhoto.previewUrl]);

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
    if (createdJobId) {
      return;
    }
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
      setError("РќРµ РЅР°СЃС‚СЂРѕРµРЅ NEXT_PUBLIC_API_BASE_URL. РЈРєР°Р¶РёС‚Рµ backend base URL РґР»СЏ СЃРѕР·РґР°РЅРёСЏ РїСЂРёРјРµСЂРєРё.");
      setWorkflowState("error");
      return;
    }
    if (!humanPhoto.file || !garmentPhoto.file) {
      setError("Р’С‹Р±РµСЂРёС‚Рµ С„РѕС‚Рѕ С‡РµР»РѕРІРµРєР° Рё С„РѕС‚Рѕ РѕРґРµР¶РґС‹.");
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
      setError(requestError instanceof Error ? requestError.message : "РќРµ СѓРґР°Р»РѕСЃСЊ СЃРѕР·РґР°С‚СЊ Р·Р°РґР°С‡Сѓ РїСЂРёРјРµСЂРєРё.");
      setWorkflowState("error");
    }
  }

  return (
    <main className="flex h-full min-w-0 flex-col overflow-hidden bg-[var(--background)]">
      <div className="border-b border-[var(--border)] bg-[var(--surface)] px-5 py-4 lg:px-6">
        <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <h1 className="workspace-title font-[family-name:var(--font-manrope)]">РќРѕРІР°СЏ РїСЂРёРјРµСЂРєР°</h1>
            <p className="workspace-subtitle mt-2 max-w-[760px] text-[var(--text-secondary)]">
              Р—Р°РіСЂСѓР·РёС‚Рµ С„РѕС‚Рѕ С‡РµР»РѕРІРµРєР° Рё С„РѕС‚Рѕ РѕРґРµР¶РґС‹. РРЅС‚РµСЂС„РµР№СЃ РѕС‚РїСЂР°РІРёС‚ С„Р°Р№Р»С‹ РЅР° Р±СЌРєРµРЅРґ Рё РїРѕРєР°Р¶РµС‚ С‚РµРєСѓС‰РёР№ СЃС‚Р°С‚СѓСЃ Р·Р°РґР°С‡Рё.
            </p>
          </div>
          <a className="site-pill-button site-pill-button--compact" href="/workspace/chat">
            Р’РµСЂРЅСѓС‚СЊСЃСЏ РІ РѕР±С‰РёР№ С‡Р°С‚
          </a>
        </div>
      </div>

      <section className="min-h-0 flex-1 overflow-hidden p-5 lg:p-6">
        <form className="tryon-layout grid h-full min-w-0 gap-5 overflow-hidden" onSubmit={handleSubmit}>
          <div className="min-h-0 overflow-y-auto overflow-x-hidden">
            <div className="grid gap-5">
              <UploadCard description={acceptedImageTypesLabel} disabled={isSubmitting} image={humanPhoto} label="Р¤РѕС‚Рѕ С‡РµР»РѕРІРµРєР°" name="human_photo" onChange={updateImage} />
              <UploadCard description={acceptedImageTypesLabel} disabled={isSubmitting} image={garmentPhoto} label="Р¤РѕС‚Рѕ РѕРґРµР¶РґС‹" name="garment_photo" onChange={updateImage} />
            </div>
          </div>

          <div className="workspace-main min-h-0 min-w-0 overflow-y-auto overflow-x-hidden">
            <div className="result-card site-card flex min-w-0 items-center justify-center p-8 lg:p-10">
              <div className="text-center">
                <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-full bg-[var(--ai-soft)] text-[2.5rem] text-[var(--ai)]">
                  {isSubmitting ? "..." : "AI"}
                </div>
                <h2 className="result-title mt-6 font-[family-name:var(--font-manrope)] font-bold tracking-[-0.04em]">
                  {workflowState === "completed" ? "Р—Р°РґР°С‡Р° Р·Р°РІРµСЂС€РµРЅР°" : "РџРѕРґРіРѕС‚РѕРІРєР° РїСЂРёРјРµСЂРєРё"}
                </h2>
                <p className="result-description mx-auto mt-4 max-w-[620px] text-[var(--text-secondary)]">
                  {createdJobId
                    ? `Р—Р°РґР°С‡Р° ${createdJobId} СЃРѕР·РґР°РЅР°. Р РµР·СѓР»СЊС‚Р°С‚ РѕС‚РєСЂРѕРµС‚СЃСЏ РїРѕСЃР»Рµ СЃС‚Р°С‚СѓСЃР° completed.`
                    : "Р’С‹Р±РµСЂРёС‚Рµ РґРІР° РёР·РѕР±СЂР°Р¶РµРЅРёСЏ Рё РѕС‚РїСЂР°РІСЊС‚Рµ РёС… РЅР° Р±СЌРєРµРЅРґ. Р“РµРЅРµСЂР°С†РёСЏ, РєР°С‡РµСЃС‚РІРѕ Рё СЃРѕС…СЂР°РЅРµРЅРёРµ РѕСЃС‚Р°СЋС‚СЃСЏ РЅР° СЃС‚РѕСЂРѕРЅРµ Р±СЌРєРµРЅРґР°."}
                </p>
                {workflowState === "status_loaded" && status ? (
                  <p className="mt-5 rounded-2xl bg-[var(--success-soft)] px-5 py-4 text-sm font-medium text-[var(--success)]">
                    РЎС‚Р°С‚СѓСЃ РїРѕР»СѓС‡РµРЅ: {status.status}. РћС‚РєСЂРѕР№С‚Рµ СЃС‚СЂР°РЅРёС†Сѓ СЂРµР·СѓР»СЊС‚Р°С‚Р°, С‡С‚РѕР±С‹ РїСЂРѕРґРѕР»Р¶РёС‚СЊ РѕС‚СЃР»РµР¶РёРІР°РЅРёРµ.
                  </p>
                ) : null}
                {resultHref ? (
                  <a className="site-pill-button mt-5" href={resultHref}>
                    РћС‚РєСЂС‹С‚СЊ Р·Р°РґР°С‡Сѓ
                  </a>
                ) : null}
                {error ? <p className="mt-5 rounded-2xl bg-[#fce8e6] px-5 py-4 text-sm font-medium text-[var(--error)]">{error}</p> : null}
              </div>
            </div>
          </div>

          <aside className="workspace-status min-h-0 overflow-y-auto overflow-x-hidden pr-1">
            <div className="site-card flex min-h-0 flex-col justify-between p-6">
              <div>
                <h2 className="text-[1.35rem] font-semibold">РЎС‚Р°С‚СѓСЃ Р±СЌРєРµРЅРґР°</h2>
                <div className="mt-6 grid gap-4">
                  <StatusHistory items={status?.status_history ?? []} />
                </div>
              </div>
              <div className="mt-6">
                <div className="mb-4 flex items-center justify-between gap-4 text-[0.95rem]">
                  <span className="text-[var(--text-secondary)]">РџРµСЃРѕС‡РЅРёС†Р°:</span>
                  <strong>СЃРїРёСЃР°РЅРёРµ РЅРµ РІС‹РїРѕР»РЅСЏРµС‚СЃСЏ</strong>
                </div>
                <SiteButton className="w-full" disabled={!canSubmit} type="submit" variant="violet">
                  {isSubmitting ? "РЎРѕР·РґР°РµРј Р·Р°РґР°С‡Сѓ..." : "РЎРѕР·РґР°С‚СЊ РїСЂРёРјРµСЂРєСѓ"}
                </SiteButton>
                <p className="mt-3 text-center text-[0.82rem] font-medium text-[var(--text-muted)]">
                  {createdJobId ? "Р—Р°РґР°С‡Р° СѓР¶Рµ СЃРѕР·РґР°РЅР°, РїРѕРІС‚РѕСЂРЅР°СЏ РѕС‚РїСЂР°РІРєР° Р·Р°Р±Р»РѕРєРёСЂРѕРІР°РЅР°" : canSubmit ? "Р¤Р°Р№Р»С‹ РіРѕС‚РѕРІС‹ Рє РѕС‚РїСЂР°РІРєРµ" : "Р—Р°РіСЂСѓР·РёС‚Рµ РѕР±Р° РёР·РѕР±СЂР°Р¶РµРЅРёСЏ РґР»СЏ РЅР°С‡Р°Р»Р°"}
                </p>
                {resultHref ? (
                  <SiteButton className="mt-4 w-full" href={resultHref} variant="soft">
                    РџРµСЂРµР№С‚Рё Рє СЃС‚Р°С‚СѓСЃСѓ
                  </SiteButton>
                ) : null}
              </div>
            </div>
          </aside>
        </form>
      </section>
    </main>
  );
}

