"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { SiteButton } from "@/components/site/site-button";
import { GarmentWearControlPicker } from "@/features/workspace/garment-wear-control-picker";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";
import type {
  TryOnGarmentSlotWearControlOptions,
  TryOnJobStatusResponse,
  TryOnPreGenerationAnalysisResponse,
  TryOnStatusEvent,
} from "@/lib/api/contracts";

type UploadRole =
  | "human_photo"
  | "garment_photo"
  | "upper_garment_photo"
  | "lower_garment_photo"
  | "outerwear_garment_photo"
  | "full_body_garment_photo";
type TryOnUploadMode = "single_item" | "upper_lower" | "upper_lower_outerwear" | "full_body";
type SelectedImage = { error: string; file: File | null; previewUrl: string };
type WorkflowState = "idle" | "submitting" | "analysis_ready" | "generating" | "status_loaded" | "completed" | "error";
type UploadCardProps = {
  description: string; disabled: boolean; image: SelectedImage; label: string; name: UploadRole;
  onChange: (role: UploadRole, file: File | null) => void;
};

const acceptedImageTypes = ["image/jpeg", "image/png", "image/webp"] as const;
const acceptedImageTypesLabel = "JPEG, PNG или WebP, до 10 МБ";
const maxFileSizeBytes = 10 * 1024 * 1024;
const emptyImage: SelectedImage = { error: "", file: null, previewUrl: "" };
const uploadModes: Array<{ id: TryOnUploadMode; label: string; description: string }> = [
  { id: "single_item", label: "Одна вещь", description: "Быстрая примерка одной вещи." },
  { id: "upper_lower", label: "Верх + низ", description: "Рубашка, футболка или худи плюс брюки, юбка или шорты." },
  { id: "upper_lower_outerwear", label: "Верх + низ + слой", description: "Образ с пальто, курткой или жакетом." },
  { id: "full_body", label: "Платье / комбинезон", description: "Цельная вещь вместо отдельных верха и низа." },
];

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
    return "Максимальный размер файла - 10 МБ.";
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

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

async function pollTryOnJobStatus(
  client: WebApiClient,
  jobId: string,
  terminalStatuses: string[],
  onStatus: (status: TryOnJobStatusResponse) => void,
): Promise<TryOnJobStatusResponse> {
  let currentStatus = await client.getJobStatus(jobId);
  onStatus(currentStatus);
  for (let attempt = 0; attempt < 30; attempt += 1) {
    if (terminalStatuses.includes(currentStatus.status)) {
      return currentStatus;
    }
    await wait(4000);
    currentStatus = await client.getJobStatus(jobId);
    onStatus(currentStatus);
  }
  return currentStatus;
}

type GarmentImages = Record<Exclude<UploadRole, "human_photo">, SelectedImage>;
type GarmentWearControls = Record<Exclude<UploadRole, "human_photo">, string>;
type GarmentImageError = { role: Exclude<UploadRole, "human_photo">; error: string };
const defaultWearControls: GarmentWearControls = {
  garment_photo: "auto",
  upper_garment_photo: "auto",
  lower_garment_photo: "auto",
  outerwear_garment_photo: "auto",
  full_body_garment_photo: "auto",
};

function requiredGarmentRolesForMode(uploadMode: TryOnUploadMode): Array<Exclude<UploadRole, "human_photo">> {
  if (uploadMode === "upper_lower") {
    return ["upper_garment_photo", "lower_garment_photo"];
  }
  if (uploadMode === "upper_lower_outerwear") {
    return ["upper_garment_photo", "lower_garment_photo", "outerwear_garment_photo"];
  }
  if (uploadMode === "full_body") {
    return ["full_body_garment_photo"];
  }
  return ["garment_photo"];
}

function requiredImagesForMode(uploadMode: TryOnUploadMode, images: GarmentImages): SelectedImage[] {
  return requiredGarmentRolesForMode(uploadMode).map((role) => images[role]);
}

function validateRequiredGarmentImages(uploadMode: TryOnUploadMode, images: GarmentImages): GarmentImageError[] {
  return requiredGarmentRolesForMode(uploadMode)
    .map((role) => ({ role, error: validateImageFile(images[role].file) }))
    .filter((item) => item.error);
}

function appendGarmentFiles(formData: FormData, uploadMode: TryOnUploadMode, images: GarmentImages): void {
  for (const role of requiredGarmentRolesForMode(uploadMode)) {
    const file = images[role].file;
    if (file) {
      formData.append(role, file);
    }
  }
}

function revokePreview(image: SelectedImage): void {
  if (image.previewUrl) {
    URL.revokeObjectURL(image.previewUrl);
  }
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
        <span className="media-zoom relative block h-[190px] w-full overflow-hidden rounded-[1.5rem]">
          <Image alt={label} className="media-zoom-media object-cover" fill src={image.previewUrl} unoptimized />
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
        <strong className="block text-[0.95rem]">Ожидание запуска</strong>
        <p className="mt-1 text-[0.85rem] leading-6 text-[var(--text-secondary)]">После отправки бэкенд вернет историю статусов задачи.</p>
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
  const [uploadMode, setUploadMode] = useState<TryOnUploadMode>("single_item");
  const [humanPhoto, setHumanPhoto] = useState<SelectedImage>(emptyImage);
  const [garmentPhoto, setGarmentPhoto] = useState<SelectedImage>(emptyImage);
  const [upperGarmentPhoto, setUpperGarmentPhoto] = useState<SelectedImage>(emptyImage);
  const [lowerGarmentPhoto, setLowerGarmentPhoto] = useState<SelectedImage>(emptyImage);
  const [outerwearGarmentPhoto, setOuterwearGarmentPhoto] = useState<SelectedImage>(emptyImage);
  const [fullBodyGarmentPhoto, setFullBodyGarmentPhoto] = useState<SelectedImage>(emptyImage);
  const [wearControls, setWearControls] = useState<GarmentWearControls>(defaultWearControls);
  const [workflowState, setWorkflowState] = useState<WorkflowState>("idle");
  const [status, setStatus] = useState<TryOnJobStatusResponse | null>(null);
  const [preGenerationAnalysis, setPreGenerationAnalysis] = useState<TryOnPreGenerationAnalysisResponse | null>(null);
  const [createdJobId, setCreatedJobId] = useState("");
  const [error, setError] = useState("");
  const isSubmitting = workflowState === "submitting" || workflowState === "generating";
  const resultHref = createdJobId ? `/workspace/try-on/result?job_id=${encodeURIComponent(createdJobId)}` : "";
  const garmentImages: GarmentImages = {
    garment_photo: garmentPhoto,
    upper_garment_photo: upperGarmentPhoto,
    lower_garment_photo: lowerGarmentPhoto,
    outerwear_garment_photo: outerwearGarmentPhoto,
    full_body_garment_photo: fullBodyGarmentPhoto,
  };
  const requiredGarmentImages = requiredImagesForMode(uploadMode, garmentImages);
  const canSubmit =
    Boolean(humanPhoto.file) &&
    !humanPhoto.error &&
    requiredGarmentImages.every((image) => image.file && !image.error) &&
    !isSubmitting &&
    !createdJobId;

  useEffect(() => {
    return () => {
      if (humanPhoto.previewUrl) {
        URL.revokeObjectURL(humanPhoto.previewUrl);
      }
    };
  }, [humanPhoto.previewUrl]);

  useEffect(() => {
    const previewUrl = garmentPhoto.previewUrl;
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [garmentPhoto.previewUrl]);

  useEffect(() => {
    const previewUrl = upperGarmentPhoto.previewUrl;
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [upperGarmentPhoto.previewUrl]);

  useEffect(() => {
    const previewUrl = lowerGarmentPhoto.previewUrl;
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [lowerGarmentPhoto.previewUrl]);

  useEffect(() => {
    const previewUrl = outerwearGarmentPhoto.previewUrl;
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [outerwearGarmentPhoto.previewUrl]);

  useEffect(() => {
    const previewUrl = fullBodyGarmentPhoto.previewUrl;
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [fullBodyGarmentPhoto.previewUrl]);

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
    updateGarmentImage(role, nextImage);
  }

  function updateGarmentImage(role: Exclude<UploadRole, "human_photo">, nextImage: SelectedImage) {
    const currentImage = garmentImages[role];
    revokePreview(currentImage);
    if (role === "garment_photo") {
      setGarmentPhoto(nextImage);
    } else if (role === "upper_garment_photo") {
      setUpperGarmentPhoto(nextImage);
    } else if (role === "lower_garment_photo") {
      setLowerGarmentPhoto(nextImage);
    } else if (role === "outerwear_garment_photo") {
      setOuterwearGarmentPhoto(nextImage);
    } else {
      setFullBodyGarmentPhoto(nextImage);
    }
  }

  function applyGarmentErrors(errors: GarmentImageError[]) {
    for (const item of errors) {
      if (item.role === "garment_photo") {
        setGarmentPhoto((current) => ({ ...current, error: item.error }));
      } else if (item.role === "upper_garment_photo") {
        setUpperGarmentPhoto((current) => ({ ...current, error: item.error }));
      } else if (item.role === "lower_garment_photo") {
        setLowerGarmentPhoto((current) => ({ ...current, error: item.error }));
      } else if (item.role === "outerwear_garment_photo") {
        setOuterwearGarmentPhoto((current) => ({ ...current, error: item.error }));
      } else {
        setFullBodyGarmentPhoto((current) => ({ ...current, error: item.error }));
      }
    }
  }

  function updateWearControl(role: Exclude<UploadRole, "human_photo">, controlCode: string) {
    setWearControls((current) => ({ ...current, [role]: controlCode }));
  }

  function slotOptions(role: Exclude<UploadRole, "human_photo">): TryOnGarmentSlotWearControlOptions | undefined {
    return preGenerationAnalysis?.slots.find((slot) => slot.slot_role === role);
  }

  function renderWearControlPicker(role: Exclude<UploadRole, "human_photo">, slotLabel: string) {
    const options = slotOptions(role);
    return (
      <GarmentWearControlPicker
        availableControls={options?.controls}
        disabled={!options}
        garmentType={options?.garment_type ?? ""}
        onSelectedControlChange={(controlCode) => updateWearControl(role, controlCode)}
        selectedControl={wearControls[role]}
        slotLabel={slotLabel}
        slotRole={role}
      />
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (createdJobId) {
      return;
    }
    setStatus(null);
    setPreGenerationAnalysis(null);

    const humanError = validateImageFile(humanPhoto.file);
    const garmentErrors = validateRequiredGarmentImages(uploadMode, garmentImages);

    if (humanError || garmentErrors.length > 0) {
      setHumanPhoto((current) => ({ ...current, error: humanError }));
      applyGarmentErrors(garmentErrors);
      setWorkflowState("error");
      return;
    }
    const baseUrl = getApiBaseUrl();
    if (!baseUrl) {
      setError("Не настроен NEXT_PUBLIC_API_BASE_URL. Укажите backend base URL для создания примерки.");
      setWorkflowState("error");
      return;
    }
    if (!humanPhoto.file || requiredGarmentImages.some((image) => !image.file)) {
      setError("Выберите фото человека и все обязательные фото одежды для выбранного режима.");
      setWorkflowState("error");
      return;
    }
    setWorkflowState("submitting");
    try {
      const formData = new FormData();
      formData.append("human_photo", humanPhoto.file);
      formData.append("sandbox_lifecycle_mode", "analysis_only");
      appendGarmentFiles(formData, uploadMode, garmentImages);
      const client = new WebApiClient(baseUrl);
      const created = await client.createTryOnJob(formData);
      setCreatedJobId(created.job_id);
      const currentStatus = await pollTryOnJobStatus(
        client,
        created.job_id,
        ["analysis_ready", "completed", "failed"],
        setStatus,
      );
      if (currentStatus.status === "analysis_ready") {
        const analysis = await client.getTryOnPreGenerationAnalysis(created.job_id);
        setPreGenerationAnalysis(analysis);
        setWorkflowState("analysis_ready");
        return;
      }
      if (currentStatus.status === "completed") {
        setWorkflowState("completed");
        router.push(`/workspace/try-on/result?job_id=${encodeURIComponent(created.job_id)}`);
        return;
      }
      if (currentStatus.status === "failed") {
        setError("Backend отклонил задачу. Проверьте фото и историю статусов ниже.");
        setWorkflowState("error");
        return;
      }
      setWorkflowState("status_loaded");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось создать задачу примерки.");
      setWorkflowState("error");
    }
  }

  async function handleGenerate() {
    setError("");
    if (!createdJobId) {
      setError("Сначала выполните анализ одежды.");
      setWorkflowState("error");
      return;
    }
    const baseUrl = getApiBaseUrl();
    if (!baseUrl) {
      setError("Не настроен NEXT_PUBLIC_API_BASE_URL. Укажите backend base URL для запуска генерации.");
      setWorkflowState("error");
      return;
    }
    setWorkflowState("generating");
    try {
      const client = new WebApiClient(baseUrl);
      if (preGenerationAnalysis) {
        const selectableSlots = preGenerationAnalysis.slots.filter((slot) => slot.controls.length > 0);
        if (selectableSlots.length > 0) {
          await client.saveTryOnWearControls(createdJobId, {
            selections: selectableSlots.map((slot) => ({
              slot_role: slot.slot_role,
              selected_control_code: wearControls[slot.slot_role] ?? slot.selected_control_code,
            })),
          });
        }
      }
      await client.continueTryOnGeneration(createdJobId);
      const currentStatus = await pollTryOnJobStatus(client, createdJobId, ["completed", "failed"], setStatus);
      if (currentStatus.status === "completed") {
        setWorkflowState("completed");
        router.push(`/workspace/try-on/result?job_id=${encodeURIComponent(createdJobId)}`);
        return;
      }
      if (currentStatus.status === "failed") {
        setError("Генерация завершилась ошибкой. Проверьте историю статусов ниже.");
        setWorkflowState("error");
        return;
      }
      setWorkflowState("status_loaded");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось запустить генерацию примерки.");
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
              Загрузите фото человека и фото одежды. Интерфейс отправит файлы на бэкенд и покажет текущий статус задачи.
            </p>
          </div>
          <a className="site-pill-button site-pill-button--compact" href="/workspace/chat">
            Вернуться в общий чат
          </a>
        </div>
      </div>

      <section className="min-h-0 flex-1 overflow-hidden p-5 lg:p-6">
        <form className="tryon-layout grid h-full min-w-0 gap-5 overflow-hidden" onSubmit={handleSubmit}>
          <div className="min-h-0 overflow-y-auto overflow-x-hidden">
            <div className="grid gap-5">
              <div className="site-card grid gap-3 p-4">
                <h2 className="upload-card-title font-semibold">Что примеряем?</h2>
                <div className="grid gap-3">
                  {uploadModes.map((mode) => (
                    <button
                      className={[
                        "rounded-[1.2rem] border px-4 py-3 text-left transition disabled:cursor-not-allowed disabled:opacity-60",
                        uploadMode === mode.id
                          ? "border-[var(--text-primary)] bg-[var(--text-primary)] text-white"
                          : "border-[var(--border)] bg-white text-[var(--text-primary)] hover:bg-[var(--surface-alt)]",
                      ].join(" ")}
                      disabled={isSubmitting || Boolean(createdJobId)}
                      key={mode.id}
                      onClick={() => setUploadMode(mode.id)}
                      type="button"
                    >
                      <strong className="block text-sm">{mode.label}</strong>
                      <span className="mt-1 block text-xs opacity-80">{mode.description}</span>
                    </button>
                  ))}
                </div>
              </div>
              <UploadCard description={acceptedImageTypesLabel} disabled={isSubmitting} image={humanPhoto} label="Фото человека" name="human_photo" onChange={updateImage} />
              {uploadMode === "single_item" ? (
                <>
                  <UploadCard description={acceptedImageTypesLabel} disabled={isSubmitting} image={garmentPhoto} label="Фото одежды" name="garment_photo" onChange={updateImage} />
                  {renderWearControlPicker("garment_photo", "Одежда")}
                </>
              ) : null}
              {uploadMode === "upper_lower" || uploadMode === "upper_lower_outerwear" ? (
                <>
                  <UploadCard description={acceptedImageTypesLabel} disabled={isSubmitting} image={upperGarmentPhoto} label="Верх" name="upper_garment_photo" onChange={updateImage} />
                  {renderWearControlPicker("upper_garment_photo", "Верх")}
                  <UploadCard description={acceptedImageTypesLabel} disabled={isSubmitting} image={lowerGarmentPhoto} label="Низ" name="lower_garment_photo" onChange={updateImage} />
                  {renderWearControlPicker("lower_garment_photo", "Низ")}
                </>
              ) : null}
              {uploadMode === "upper_lower_outerwear" ? (
                <>
                  <UploadCard description={acceptedImageTypesLabel} disabled={isSubmitting} image={outerwearGarmentPhoto} label="Верхний слой" name="outerwear_garment_photo" onChange={updateImage} />
                  {renderWearControlPicker("outerwear_garment_photo", "Верхний слой")}
                </>
              ) : null}
              {uploadMode === "full_body" ? (
                <>
                  <UploadCard description={acceptedImageTypesLabel} disabled={isSubmitting} image={fullBodyGarmentPhoto} label="Платье / комбинезон" name="full_body_garment_photo" onChange={updateImage} />
                  {renderWearControlPicker("full_body_garment_photo", "Цельная вещь")}
                </>
              ) : null}
            </div>
          </div>

          <div className="workspace-main min-h-0 min-w-0 overflow-y-auto overflow-x-hidden">
            <div className="result-card site-card flex min-w-0 items-center justify-center p-8 lg:p-10">
              <div className="text-center">
                <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-full bg-[var(--ai-soft)] text-[2.5rem] text-[var(--ai)]">
                  {isSubmitting ? "..." : "AI"}
                </div>
                <h2 className="result-title mt-6 font-[family-name:var(--font-manrope)] font-bold tracking-[-0.04em]">
                  {workflowState === "completed" ? "Задача завершена" : workflowState === "analysis_ready" ? "Анализ готов" : "Подготовка примерки"}
                </h2>
                <p className="result-description mx-auto mt-4 max-w-[620px] text-[var(--text-secondary)]">
                  {createdJobId
                    ? preGenerationAnalysis
                      ? `Задача ${createdJobId} проанализирована. Проверьте варианты ношения и запустите генерацию.`
                      : `Задача ${createdJobId} создана. Результат откроется после статуса completed.`
                    : "Выберите изображения и отправьте их на backend-анализ. Генерация запустится отдельным шагом после проверки вариантов ношения."}
                </p>
                {preGenerationAnalysis ? (
                  <div className="mt-5 rounded-2xl bg-[var(--ai-soft)] px-5 py-4 text-left text-sm text-[var(--text-primary)]">
                    <strong className="block">Backend распознал одежду</strong>
                    <div className="mt-3 grid gap-2">
                      {preGenerationAnalysis.slots.map((slot) => (
                        <p className="text-[0.85rem] leading-6 text-[var(--text-secondary)]" key={slot.slot_role}>
                          {slot.slot_role}: {slot.garment_type}. Доступно вариантов: {slot.controls.length}.
                        </p>
                      ))}
                    </div>
                  </div>
                ) : null}
                {workflowState === "status_loaded" && status ? (
                  <p className="mt-5 rounded-2xl bg-[var(--success-soft)] px-5 py-4 text-sm font-medium text-[var(--success)]">
                    Статус получен: {status.status}. Откройте страницу результата, чтобы продолжить отслеживание.
                  </p>
                ) : null}
                {resultHref ? (
                  <a className="site-pill-button mt-5" href={resultHref}>
                    Открыть задачу
                  </a>
                ) : null}
                {error ? <p className="mt-5 rounded-2xl bg-[#fce8e6] px-5 py-4 text-sm font-medium text-[var(--error)]">{error}</p> : null}
              </div>
            </div>
          </div>

          <aside className="workspace-status min-h-0 overflow-y-auto overflow-x-hidden pr-1">
            <div className="site-card flex min-h-0 flex-col justify-between p-6">
              <div>
                <h2 className="text-[1.35rem] font-semibold">Статус бэкенда</h2>
                <div className="mt-6 grid gap-4">
                  <StatusHistory items={status?.status_history ?? []} />
                </div>
              </div>
              <div className="mt-6">
                <div className="mb-4 flex items-center justify-between gap-4 text-[0.95rem]">
                  <span className="text-[var(--text-secondary)]">Песочница:</span>
                  <strong>списание не выполняется</strong>
                </div>
                <SiteButton className="w-full" disabled={!canSubmit} type="submit" variant="violet">
                  {workflowState === "submitting" ? "Анализируем..." : "Сначала проанализировать"}
                </SiteButton>
                {preGenerationAnalysis ? (
                  <SiteButton
                    className="mt-4 w-full"
                    disabled={workflowState === "generating"}
                    onClick={handleGenerate}
                    type="button"
                    variant="violet"
                  >
                    {workflowState === "generating" ? "Генерируем..." : "Запустить генерацию"}
                  </SiteButton>
                ) : null}
                <p className="mt-3 text-center text-[0.82rem] font-medium text-[var(--text-muted)]">
                  {preGenerationAnalysis ? "Можно выбрать способ ношения и запускать генерацию" : createdJobId ? "Задача уже создана, повторная отправка заблокирована" : canSubmit ? "Файлы готовы к анализу" : "Загрузите обязательные изображения для начала"}
                </p>
                {resultHref ? (
                  <SiteButton className="mt-4 w-full" href={resultHref} variant="soft">
                    Перейти к статусу
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
