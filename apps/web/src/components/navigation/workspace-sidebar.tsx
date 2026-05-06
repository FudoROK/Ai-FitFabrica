import Link from "next/link";
import { workspaceRoutes } from "@/lib/routes/workspace-routes";

type WorkspaceSidebarProps = {
  currentPath: string;
};

export function WorkspaceSidebar({
  currentPath
}: WorkspaceSidebarProps) {
  return (
    <aside className="workspace-sidebar">
      <div className="mb-8">
        <p className="site-logo">FitFabrica Workspace</p>
        <p className="mt-2 text-sm text-[var(--text-secondary)]">Рабочая оболочка для продуктовых сценариев</p>
      </div>
      <nav className="flex flex-col gap-2">
        {workspaceRoutes.map((route) => {
          const isActive = currentPath === route.href;

          return (
            <Link
              key={route.href}
              className={isActive ? "workspace-link workspace-link-active" : "workspace-link"}
              href={route.href}
            >
              {route.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
