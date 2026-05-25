"use client";

import Image from "next/image";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";
import type { TryOnResult, TryOnResultResponse } from "@/lib/api/contracts";
import { WebApiClient } from "@/lib/api/client";

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
}

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function ResultImage({ result }: { result: TryOnResult }) {
  const imageUrl = result.result_image.url.trim();
  const imageAlt = result.result_image.alt.trim() || "Sandbox Try-On result preview";

  if (!imageUrl) {
    return <ImagePlaceholder className="h-[460px] w-full" label={imageAlt} />;
  }

  return (
    <Image
      alt={imageAlt}
      className="h-[460px] w-full rounded-[2rem] object-cover"
      height={900}
      priority
      src={imageUrl}
      unoptimized
      width={1200}
    />
  );
}

export function TryOnResultView() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("job_id");
  const [response, setResponse] = useState<TryOnResultResponse | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function loadResult() {
      setIsLoading(true);
      setResponse(null);
      setError("");

      if (!jobId) {
        setError("Не указан job_id для результата примерки.");
        setIsLoading(false);
        return;
      }

      const baseUrl = getApiBaseUrl();
      if (!baseUrl) {
        setError("Не настроен NEXT_PUBLIC_API_BASE_URL для загрузки результата Try-On.");
        setIsLoading(false);
        return;
      }

      try {
        const client = new WebApiClient(baseUrl);
        const result = await client.getJobResult(jobId);

        if (isMounted) {
          setResponse(result);
        }
      } catch (requestError) {
        if (isMounted) {
          setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить результат Try-On.");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadResult();

    return () => {
      isMounted = false;
    };
  }, [jobId]);

  if (isLoading) {
    return <main className="px-8 py-10 lg:px-16">Загружаем результат Try-On...</main>;
  }

  if (error) {
    return (
      <main className="px-8 py-10 lg:px-16">
        <div className="site-card p-8">
          <h1 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold tracking-[-0.04em]">
            Результат недоступен
          </h1>
          <p className="mt-4 text-[var(--text-secondary)]">{error}</p>
          <SiteButton className="mt-8" href="/workspace/try-on/new" variant="primary">
            Создать новую примерку
          </SiteButton>
        </div>
      </main>
    );
  }

  if (!response || response.status === "not_ready") {
    return (
      <main className="px-8 py-10 lg:px-16">
        <div className="site-card p-8">
          <h1 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold tracking-[-0.04em]">
            Workflow еще выполняется
          </h1>
          <p className="mt-4 text-[var(--text-secondary)]">
            Текущий статус: {response?.status === "not_ready" ? response.current_status : "unknown"}.
          </p>
          {response?.status === "not_ready" ? (
            <p className="mt-3 break-all text-sm text-[var(--text-secondary)]">Status endpoint: {response.status_url}</p>
          ) : null}
          <div className="mt-8 flex flex-wrap gap-4">
            <SiteButton href="/workspace/try-on/new" variant="secondary">
              Вернуться к примерке
            </SiteButton>
            <SiteButton onClick={() => window.location.reload()} variant="violet">
              Проверить снова
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
        <SiteButton href="/workspace/try-on/new" variant="secondary">
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
              Quality report
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
              {result.quality_report.checks.map((check) => (
                <div className="rounded-[1.5rem] bg-white px-5 py-4 text-[0.95rem]" key={check.name}>
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
                <strong className="block text-[var(--text-primary)]">Limitations</strong>
                <ul className="mt-3 grid gap-2">
                  {result.quality_report.limitations.map((limitation) => (
                    <li key={limitation}>{limitation}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </article>

          {result.input_metadata.length > 0 ? (
            <article className="site-card p-6">
              <h2 className="font-[family-name:var(--font-manrope)] text-[1.7rem] font-bold">Input metadata</h2>
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
