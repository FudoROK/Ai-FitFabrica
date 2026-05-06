"use client";

import { usePathname } from "next/navigation";
import { WorkspaceSidebar } from "@/components/navigation/workspace-sidebar";

export default function WorkspaceLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  const pathname = usePathname();

  return (
    <div className="workspace-layout">
      <WorkspaceSidebar currentPath={pathname} />
      <div className="workspace-main">{children}</div>
    </div>
  );
}
