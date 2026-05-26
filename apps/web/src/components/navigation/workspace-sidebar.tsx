"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { SiteButton } from "@/components/site/site-button";
import { workspaceRoutes } from "@/lib/routes/workspace-routes";

type WorkspaceSidebarProps = {
  currentPath: string;
};

function isRouteActive(currentPath: string, href: string): boolean {
  if (href === "/workspace") {
    return currentPath === href;
  }

  if (currentPath === href || currentPath.startsWith(`${href}/`)) {
    return true;
  }

  if (href === "/workspace/new-fitting" && currentPath === "/workspace/try-on/result") {
    return true;
  }

  if (href === "/workspace/product-card" && currentPath === "/workspace/content-package") {
    return true;
  }

  return false;
}

function AvatarBlock({ collapsed }: { collapsed: boolean }) {
  return (
    <div className="flex items-center gap-3 rounded-[1rem] border border-[var(--border)] bg-[var(--surface)] px-3 py-3">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--surface-alt)] text-sm font-semibold">
        A
      </div>
      {collapsed ? null : (
        <div className="min-w-0">
          <p className="truncate text-[0.92rem] font-semibold text-black">Анна С.</p>
          <p className="truncate text-[0.78rem] text-[var(--text-secondary)]">Личный рабочий кабинет</p>
        </div>
      )}
    </div>
  );
}

export function WorkspaceSidebar({ currentPath }: WorkspaceSidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    function syncCollapsedState() {
      setCollapsed(window.innerWidth < 1440);
    }

    syncCollapsedState();
    window.addEventListener("resize", syncCollapsedState);

    return () => {
      window.removeEventListener("resize", syncCollapsedState);
    };
  }, []);

  return (
    <aside className={`workspace-sidebar ${collapsed ? "sidebar-collapsed" : "sidebar-expanded"} shrink-0 border-r border-[var(--border)] bg-[var(--surface)] px-3 py-4 transition-[width] duration-200`}>
      <div className="flex h-full flex-col">
        <div className={`flex items-start gap-2 pb-3 ${collapsed ? "justify-end" : "justify-between"}`}>
          {collapsed ? <div aria-hidden="true" /> : <div className="font-[family-name:var(--font-manrope)] text-[1.45rem] font-bold tracking-[-0.04em]">Рабочий кабинет FitFabrica</div>}
          <button
            aria-label={collapsed ? "Развернуть панель" : "Свернуть панель"}
            className="sidebar-item flex h-10 min-w-[4.5rem] shrink-0 items-center justify-center border border-[var(--border)] bg-[var(--background)] px-2 text-[0.8rem] font-semibold text-[var(--text-secondary)] transition hover:bg-black/4 hover:text-black"
            onClick={() => setCollapsed((current) => !current)}
            type="button"
          >
            {collapsed ? "Развернуть" : "Свернуть"}
          </button>
        </div>

        <div className="mt-4">
          <AvatarBlock collapsed={collapsed} />
        </div>

        {!collapsed ? (
          <div className="mt-4 flex-1 min-h-0 overflow-y-auto overflow-x-hidden pr-1">
            <div className="inline-flex items-center gap-2 text-[0.88rem] font-medium text-[var(--text-secondary)] transition hover:text-black">
              <Link href="/workspace" title="Вернуться в общий чат">
                Вернуться в общий чат
              </Link>
            </div>

            <SiteButton className="mt-4 w-full" href="/workspace/new-fitting" variant="violet">
              Новая примерка
            </SiteButton>

            <div className="mt-5 text-[0.76rem] font-semibold uppercase tracking-[0.18em] text-[var(--text-muted)]">Рабочие разделы</div>

            <nav className="mt-3 flex flex-col gap-1">
              {workspaceRoutes.map((route) => {
                const active = isRouteActive(currentPath, route.href);

                return (
                  <Link
                    className={`sidebar-item flex items-center px-3 transition ${
                      active
                        ? "bg-[rgba(124,92,255,0.10)] text-[#6D5DF6]"
                        : "text-[var(--text-secondary)] hover:bg-black/4 hover:text-black"
                    }`}
                    href={route.href}
                    key={route.href}
                  >
                    <span className="truncate">{route.label}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
        ) : (
          <div className="mt-4 flex-1" />
        )}

        <div className="mt-auto pt-4">
          <SiteButton className="w-full" href="/workspace/style-profile" variant="primary">
            {collapsed ? "Профиль" : "Профиль пользователя"}
          </SiteButton>
          {!collapsed ? (
            <p className="mt-2 text-[0.78rem] text-[var(--text-secondary)]">
              Заполните профиль, чтобы сохранить параметры стиля и примерок.
            </p>
          ) : null}
        </div>
      </div>
    </aside>
  );
}
