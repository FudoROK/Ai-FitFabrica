"use client";

import Image from "next/image";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";
import type { TryOnJobStatusResponse, TryOnResult, TryOnResultResponse } from "@/lib/api/contracts";
import { WebApiClient } from "@/lib/api/client";

const safeJobIdPattern = /^[A-Za-z0-9_-]+$/;
const pollingDelayMs = 2500;

type LoadResultOptions = {
  showLoading?: boolean;
};

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
}

function percent(value: number): string {
  const clampedValue = Math.min(1, Math.max(0, value));
  return `${Math.round(clampedValue * 100)}%`;
}

function ResultImage({ result }: { result: TryOnResult }) {
  const imageUrl = result.result_image.url.trim();
  const imageAlt = result.result_image.alt.trim() || "Предпросмотр результата примерки";

  if (!imageUrl) {
    return <ImagePlaceholder className="h-[460px] w-full" label={imageAlt} />;
  }

  return (
    <div className="media-zoom overflow-hidden rounded-[2rem]">
      <Image
        alt={imageAlt}
        className="media-zoom-media h-[460px] w-full object-cover"
        height={900}
        priority
        src={imageUrl}
        unoptimized
        width={1200}
      />
    </div>
  );
}

export function TryOnResultView() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("job_id");
  const isMountedRef = useRef(false);
  const pollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [response, setResponse] = useState<TryOnResultResponse | null>(null);
  const [statusResponse, setStatusResponse] = useState<TryOnJobStatusResponse | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pollAttempt, setPollAttempt] = useState(0);

  const clearPendingPoll = useCallback(() => {
    if (pollTimeoutRef.current) {
      clearTimeout(pollTimeoutRef.current);
      pollTimeoutRef.current = null;
    }
  }, []);

  const loadResult = useCallback(async ({ showLoading = false }: LoadResultOptions = {}) => {
    clearPendingPoll();

    if (showLoading) {
      setIsLoading(true);
      setResponse(null);
      setStatusResponse(null);
    } else {
      setIsRefreshing(true);
    }
    setError("");

    const normalizedJobId = jobId?.trim() ?? "";

    if (!normalizedJobId) {
      setError("Параметр job_id не указан.");
      setIsLoading(false);
      setIsRefreshing(false);
      return;
    }

    if (!safeJobIdPattern.test(normalizedJobId)) {
      setError("Параметр job_id содержит недопустимые символы.");
      setIsLoading(false);
      setIsRefreshing(false);
      return;
    }

    const baseUrl = getApiBaseUrl();
    if (!baseUrl) {
      setError("Не настроен NEXT_PUBLIC_API_BASE_URL для чтения результата примерки.");
      setIsLoading(false);
      setIsRefreshing(false);
      return;
    }

    try {
      const client = new WebApiClient(baseUrl);
      const result = await client.getJobResult(normalizedJobId);

      if (!isMountedRef.current) {
        return;
      }

      setResponse(result);

      if (result.status === "not_ready") {
        const latestStatus = await client.getJobStatus(normalizedJobId);

        if (!isMountedRef.current) {
          return;
        }

        setStatusResponse(latestStatus);

        if (latestStatus.status === "failed") {
          setError("Задача примерки завершилась ошибкой. Проверьте статус и попробуйте снова.");
          return;
        }

        pollTimeoutRef.current = setTimeout(() => {
          setPollAttempt((current) => current + 1);
        }, pollingDelayMs);
        return;
      }

      setStatusResponse(null);
    } catch (requestError) {
      if (isMountedRef.current) {
        setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить результат примерки.");
      }
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    }
  }, [clearPendingPoll, jobId]);

  useEffect(() => {
    isMountedRef.current = true;

    const startTimer = setTimeout(() => {
      void loadResult({ showLoading: pollAttempt === 0 });
    }, 0);

    return () => {
      isMountedRef.current = false;
      clearTimeout(startTimer);
      clearPendingPoll();
    };
  }, [clearPendingPoll, loadResult, pollAttempt]);

  if (isLoading) {
    return <main className="px-8 py-10 lg:px-16">Загружаем результат примерки...</main>;
  }

  if (error && (!response || response.status !== "not_ready")) {
    return (
      <main className="px-8 py-10 lg:px-16">
        <div className="site-card p-8">
          <h1 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold tracking-[-0.04em]">
            Не удалось открыть результат
          </h1>
          <p className="mt-4 text-[var(--text-secondary)]">{error}</p>
          <SiteButton className="mt-8" href="/workspace/new-fitting" variant="primary">
            Начать новую примерку
          </SiteButton>
        </div>
      </main>
    );
  }

  if (!response || response.status === "not_ready") {
    const currentStatus = statusResponse?.status ?? (response?.status === "not_ready" ? response.current_status : "unknown");
    const statusHistory = statusResponse?.status_history ?? [];

    return (
      <main className="px-8 py-10 lg:px-16">
        <div className="site-card p-8">
          <h1 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold tracking-[-0.04em]">
            Workflow еще выполняется
          </h1>
          <p className="mt-4 text-[var(--text-secondary)]">Текущий статус: {currentStatus}.</p>
          {response?.status === "not_ready" ? (
            <p className="mt-3 break-all text-sm text-[var(--text-secondary)]">Status endpoint: {response.status_url}</p>
          ) : null}
          {error ? <p className="mt-5 rounded-2xl bg-[#fce8e6] px-5 py-4 text-sm font-medium text-[var(--error)]">{error}</p> : null}
          {statusHistory.length > 0 ? (
            <div className="mt-6 grid gap-3">
              {statusHistory.map((item) => (
                <div className="rounded-[1.2rem] bg-[var(--background)] p-4" key={`${item.status}-${item.occurred_at}`}>
                  <strong className="block text-[0.95rem]">{item.stage}</strong>
                  <p className="mt-1 text-[0.85rem] leading-6 text-[var(--text-secondary)]">{item.message}</p>
                </div>
              ))}
            </div>
          ) : null}
          <div className="mt-8 flex flex-wrap gap-4">
            <SiteButton href="/workspace/new-fitting" variant="secondary">
              Вернуться к загрузке
            </SiteButton>
            <SiteButton disabled={isRefreshing || currentStatus === "failed"} onClick={() => void loadResult()} variant="violet">
              {isRefreshing ? "Обновляем..." : "Проверить статус"}
            </SiteButton>
          </div>
        </div>
      </main>
    );
  }

  const result = response.result;

  return (
    <main className="px-8 py-10 lg:px-16">
      <div className="flex flex-wrap items-start justify-between gap-6">
        <div>
          <h1 className="font-[family-name:var(--font-manrope)] text-[clamp(2.6rem,5vw,4.6rem)] font-bold tracking-[-0.04em]">
            Результат примерки
          </h1>
          <p className="mt-3 text-[1.1rem] text-[var(--text-secondary)]">Job {result.job_id}</p>
        </div>
        <SiteButton href="/workspace/new-fitting" variant="secondary">
          Новая примерка
        </SiteButton>
      </div>

      <section className="mt-10 grid gap-8 xl:grid-cols-[1fr_360px]">
        <div>
          <ResultImage result={result} />
          <article className="site-card mt-8 p-6">
            <h2 className="font-[family-name:var(--font-manrope)] text-[2rem] font-bold tracking-[-0.03em]">
              Комментарий стилиста
            </h2>
            <p className="mt-5 leading-8 text-[var(--text-secondary)]">{result.stylist_note}</p>
          </article>
        </div>

        <div className="grid gap-8">
          <article className="rounded-[2rem] border border-[#c7b8ff] bg-[#ede6ff] p-6">
            <h2 className="font-[family-name:var(--font-manrope)] text-[2rem] font-bold text-[#2f2570]">
              Отчет по качеству
            </h2>
            <div className="mt-5 grid gap-3 text-[0.95rem] text-[var(--text-secondary)]">
              <p>
                Verdict: <strong className="text-[#2f2570]">{result.quality_report.verdict}</strong>
              </p>
              <p>
                Confidence: <strong className="text-[#2f2570]">{percent(result.quality_report.confidence)}</strong>
              </p>
            </div>

            <div className="mt-6 grid gap-4">
              {result.quality_report.checks.map((check, index) => (
                <div className="rounded-[1.5rem] bg-white px-5 py-4 text-[0.95rem]" key={`${check.name}-${index}`}>
                  <div className="flex items-center justify-between gap-3">
                    <strong>{check.name}</strong>
                    <span className="text-sm font-semibold text-[#2f2570]">{percent(check.confidence)}</span>
                  </div>
                  <p className="mt-1 text-sm text-[var(--text-secondary)]">Status: {check.status}</p>
                  <p className="mt-2 leading-6 text-[var(--text-secondary)]">{check.message}</p>
                </div>
              ))}
            </div>

            {result.quality_report.limitations.length > 0 ? (
              <div className="mt-6 rounded-[1.5rem] bg-white/70 px-5 py-4 text-[0.9rem] text-[var(--text-secondary)]">
                <strong className="block text-[var(--text-primary)]">Ограничения</strong>
                <ul className="mt-3 grid gap-2">
                  {result.quality_report.limitations.map((limitation, index) => (
                    <li key={`${limitation}-${index}`}>{limitation}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </article>

          {result.input_metadata.length > 0 ? (
            <article className="site-card p-6">
              <h2 className="font-[family-name:var(--font-manrope)] text-[1.7rem] font-bold">Метаданные входных файлов</h2>
              <div className="mt-5 grid gap-3">
                {result.input_metadata.map((item) => (
                  <div className="rounded-[1.25rem] bg-[var(--background)] p-4 text-sm" key={`${item.role}-${item.sha256}`}>
                    <strong>{item.role}</strong>
                    <p className="mt-1 break-all text-[var(--text-secondary)]">{item.filename}</p>
                    <p className="mt-1 text-[var(--text-secondary)]">
                      {item.content_type}, {item.size_bytes} bytes
                    </p>
                  </div>
                ))}
              </div>
            </article>
          ) : null}
        </div>
      </section>
    </main>
  );
}
