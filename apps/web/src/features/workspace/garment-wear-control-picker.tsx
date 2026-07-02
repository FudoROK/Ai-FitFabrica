"use client";

import { useEffect, useState } from "react";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";
import type { GarmentWearControlResponse } from "@/lib/api/contracts";

type WearControlState = "idle" | "loading" | "ready" | "empty" | "error";

export type GarmentWearControlPickerProps = {
  availableControls?: GarmentWearControlResponse[];
  disabled: boolean;
  garmentType: string;
  onSelectedControlChange: (controlCode: string) => void;
  selectedControl: string;
  slotLabel: string;
  slotRole: string;
};

export function GarmentWearControlPicker({
  availableControls,
  disabled,
  garmentType,
  onSelectedControlChange,
  selectedControl,
  slotLabel,
  slotRole,
}: GarmentWearControlPickerProps) {
  const normalizedGarmentType = garmentType.trim();
  const hasResolvedControls = availableControls !== undefined;
  const canLoadControls = (hasResolvedControls || Boolean(normalizedGarmentType)) && !disabled;
  const [controls, setControls] = useState<GarmentWearControlResponse[]>([]);
  const [state, setState] = useState<WearControlState>("idle");
  const [error, setError] = useState("");
  const displayControls = availableControls ?? controls;
  const displayState: WearControlState = hasResolvedControls
    ? availableControls.length > 0
      ? "ready"
      : "empty"
    : state;

  useEffect(() => {
    if (!canLoadControls || hasResolvedControls) {
      return;
    }

    let active = true;
    async function loadControls() {
      setState("loading");
      setError("");
      try {
        const baseUrl = getApiBaseUrl();
        if (!baseUrl) {
          throw new Error("Backend URL is not configured.");
        }
        const client = new WebApiClient(baseUrl);
        const response = await client.getGarmentWearControls(normalizedGarmentType);
        if (!active) {
          return;
        }
        setControls(response.controls);
        setState(response.controls.length ? "ready" : "empty");
      } catch (requestError) {
        if (!active) {
          return;
        }
        setError(requestError instanceof Error ? requestError.message : "Could not load wear controls.");
        setControls([]);
        setState("error");
      }
    }

    void loadControls();

    return () => {
      active = false;
    };
  }, [canLoadControls, hasResolvedControls, normalizedGarmentType]);

  if (!canLoadControls) {
    return (
      <section
        aria-label={`Wear controls for ${slotLabel}`}
        className="wear-control-pending-analysis rounded-[1.25rem] border border-dashed border-[var(--border)] bg-[var(--surface-alt)] p-4"
        data-slot-role={slotRole}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-[var(--text-primary)]">Как носить: авто</p>
            <p className="mt-1 text-xs leading-5 text-[var(--text-secondary)]">
              Варианты появятся после backend-анализа одежды. Сейчас система сама выберет безопасный способ ношения.
            </p>
          </div>
          <span className="rounded-full bg-[var(--ai-soft)] px-3 py-1 text-[0.72rem] font-semibold text-[var(--ai)]">
            pending analysis
          </span>
        </div>
      </section>
    );
  }

  return (
    <section
      aria-label={`Wear controls for ${slotLabel}`}
      className="rounded-[1.25rem] border border-[var(--border)] bg-[var(--surface)] p-4"
      data-slot-role={slotRole}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-[var(--text-primary)]">Как носить: {slotLabel}</p>
          <p className="mt-1 text-xs leading-5 text-[var(--text-secondary)]">
            Backend отдаёт только разрешённые варианты для распознанного типа одежды.
          </p>
        </div>
        <span className="rounded-full bg-[var(--success-soft)] px-3 py-1 text-[0.72rem] font-semibold text-[var(--success)]">
          backend-driven
        </span>
      </div>

      {displayState === "loading" ? <p className="mt-4 text-xs font-medium text-[var(--text-muted)]">Загружаем варианты...</p> : null}
      {displayState === "error" ? <p className="mt-4 text-xs font-semibold text-[var(--error)]">{error}</p> : null}
      {displayState === "empty" ? (
        <p className="mt-4 text-xs font-medium text-[var(--text-muted)]">
          Для этого типа одежды пока нет approved вариантов. Будет использован backend auto mode.
        </p>
      ) : null}
      {displayState === "ready" ? (
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            className={[
              "rounded-full border px-3 py-2 text-xs font-semibold transition",
              selectedControl === "auto"
                ? "border-[var(--text-primary)] bg-[var(--text-primary)] text-white"
                : "border-[var(--border)] bg-white text-[var(--text-primary)] hover:bg-[var(--surface-alt)]",
            ].join(" ")}
            onClick={() => onSelectedControlChange("auto")}
            type="button"
          >
            Авто
          </button>
          {displayControls.map((control) => (
            <button
              className={[
                "rounded-full border px-3 py-2 text-xs font-semibold transition",
                selectedControl === control.control_code
                  ? "border-[var(--text-primary)] bg-[var(--text-primary)] text-white"
                  : "border-[var(--border)] bg-white text-[var(--text-primary)] hover:bg-[var(--surface-alt)]",
              ].join(" ")}
              key={control.control_code}
              onClick={() => onSelectedControlChange(control.control_code)}
              title={control.description ?? control.instruction_template}
              type="button"
            >
              {control.display_name}
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
