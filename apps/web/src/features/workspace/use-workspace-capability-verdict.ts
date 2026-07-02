"use client";

import { useEffect, useState } from "react";
import type { WorkspaceCapability, WorkspaceCapabilityMatrixResponse } from "@/lib/api/contracts";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";

type WorkspaceCapabilityVerdict = {
  error: string;
  matrix: WorkspaceCapabilityMatrixResponse | null;
  publishVerdict: string;
};

type WorkspaceCapabilityVerdictOptions = {
  capabilityForAssert?: WorkspaceCapability;
  enabled: boolean;
};

export function useWorkspaceCapabilityVerdict(
  options: WorkspaceCapabilityVerdictOptions,
): WorkspaceCapabilityVerdict {
  const { capabilityForAssert, enabled } = options;
  const [matrix, setMatrix] = useState<WorkspaceCapabilityMatrixResponse | null>(null);
  const [error, setError] = useState("");
  const [publishVerdict, setPublishVerdict] = useState("");

  useEffect(() => {
    let isActive = true;

    async function loadVerdict() {
      try {
        const client = new WebApiClient(getApiBaseUrl());
        const nextMatrix = await client.getWorkspaceCapabilities();
        if (!isActive) {
          return;
        }
        setMatrix(nextMatrix);
        setError("");

        if (!capabilityForAssert) {
          setPublishVerdict("");
          return;
        }

        try {
          await client.assertWorkspaceCapability(capabilityForAssert);
          if (isActive) {
            setPublishVerdict("Server preflight: publish capability confirmed.");
          }
        } catch (requestError) {
          if (isActive) {
            setPublishVerdict(requestError instanceof Error ? requestError.message : "Server preflight failed.");
          }
        }
      } catch (requestError) {
        if (!isActive) {
          return;
        }
        setMatrix(null);
        setError(requestError instanceof Error ? requestError.message : "Failed to load capability matrix.");
      }
    }

    if (enabled) {
      void loadVerdict();
    }

    return () => {
      isActive = false;
    };
  }, [capabilityForAssert, enabled]);

  return { matrix, publishVerdict, error };
}
