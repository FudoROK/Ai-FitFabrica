"use client";

import { usePathname } from "next/navigation";
import { WorkspaceSidebar } from "@/components/navigation/workspace-sidebar";
import { WorkspaceRuntimeProvider, useWorkspaceRuntime } from "@/features/workspace/workspace-runtime";
import { WorkspaceShellError } from "@/features/workspace/workspace-shell-error";
import { WorkspaceShellLoading } from "@/features/workspace/workspace-shell-loading";

function WorkspaceLayoutBody({ children }: Readonly<{ children: React.ReactNode }>) {
  const pathname = usePathname();
  const { bootstrap, error, isLoading, refresh } = useWorkspaceRuntime();

  if (isLoading) {
    return <WorkspaceShellLoading />;
  }

  if (error && bootstrap === null) {
    return <WorkspaceShellError error={error} onRetry={refresh} />;
  }

  return (
    <div className="workspace-shell bg-[var(--background)]">
      <div className="workspace-desktop-layout hidden h-full min-w-0 lg:flex">
        <WorkspaceSidebar currentPath={pathname} />
        <div className="workspace-content-pane min-w-0 flex-1 overflow-y-auto overflow-x-hidden">{children}</div>
      </div>

      <div className="h-full overflow-y-auto lg:hidden">
        <WorkspaceSidebar currentPath={pathname} />
        <div>{children}</div>
      </div>
    </div>
  );
}

export default function WorkspaceLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <WorkspaceRuntimeProvider>
      <WorkspaceLayoutBody>{children}</WorkspaceLayoutBody>
    </WorkspaceRuntimeProvider>
  );
}
