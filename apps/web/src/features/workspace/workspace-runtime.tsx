"use client";

import { createContext, useContext, useEffect, useState } from "react";
import type { WorkspaceBootstrapResponse, WorkspaceCapability } from "@/lib/api/contracts";
import { WebApiClient } from "@/lib/api/client";
import { getApiBaseUrl } from "@/lib/api/config";

type WorkspaceRuntimeValue = {
  bootstrap: WorkspaceBootstrapResponse | null;
  error: string;
  hasCapability: (capability: WorkspaceCapability) => boolean;
  isLoading: boolean;
  refresh: () => Promise<void>;
};

const WorkspaceRuntimeContext = createContext<WorkspaceRuntimeValue | null>(null);

async function fetchBootstrap(): Promise<WorkspaceBootstrapResponse> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new Error("Workspace API base URL is not configured.");
  }

  return new WebApiClient(baseUrl).getWorkspaceBootstrap();
}

export function WorkspaceRuntimeProvider({ children }: { children: React.ReactNode }) {
  const [bootstrap, setBootstrap] = useState<WorkspaceBootstrapResponse | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  async function refresh() {
    setIsLoading(true);
    setError("");
    try {
      setBootstrap(await fetchBootstrap());
    } catch (requestError) {
      setBootstrap(null);
      setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить рабочую зону.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    let isActive = true;

    async function loadOnMount() {
      try {
        const nextBootstrap = await fetchBootstrap();
        if (!isActive) {
          return;
        }
        setBootstrap(nextBootstrap);
      } catch (requestError) {
        if (!isActive) {
          return;
        }
        setBootstrap(null);
        setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить рабочую зону.");
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadOnMount();

    return () => {
      isActive = false;
    };
  }, []);

  return (
    <WorkspaceRuntimeContext.Provider
      value={{
        bootstrap,
        error,
        hasCapability(capability) {
          return bootstrap?.capabilities.includes(capability) ?? false;
        },
        isLoading,
        refresh,
      }}
    >
      {children}
    </WorkspaceRuntimeContext.Provider>
  );
}

export function useWorkspaceRuntime() {
  const context = useContext(WorkspaceRuntimeContext);

  if (context === null) {
    throw new Error("Workspace runtime context is required.");
  }

  return context;
}
