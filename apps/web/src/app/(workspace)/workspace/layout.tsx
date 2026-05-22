"use client";

import { usePathname } from "next/navigation";
import { WorkspaceSidebar } from "@/components/navigation/workspace-sidebar";

export default function WorkspaceLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  const pathname = usePathname();

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
