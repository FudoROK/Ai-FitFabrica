"use client";

import { useEffect, useState } from "react";
import { SiteButton } from "@/components/site/site-button";
import { WorkspaceCapabilityCta } from "@/features/workspace/workspace-capability-cta";
import { useWorkspaceRuntime } from "@/features/workspace/workspace-runtime";
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

  if (href === "/workspace/new-fitting" && currentPath.startsWith("/workspace/try-on")) {
    return true;
  }

  if (href === "/workspace/product-card" && currentPath === "/workspace/content-package") {
    return true;
  }

  if (href === "/workspace/projects" && currentPath === "/workspace/history") {
    return true;
  }

  if (
    href === "/workspace/settings" &&
    (currentPath === "/workspace/style-profile" ||
      currentPath === "/workspace/business-profile" ||
      currentPath === "/workspace/integrations")
  ) {
    return true;
  }

  return false;
}

export function WorkspaceSidebar({ currentPath }: WorkspaceSidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const { bootstrap } = useWorkspaceRuntime();

  useEffect(() => {
    function syncCollapsedState() {
      setCollapsed(window.innerWidth < 1280);
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
          {collapsed ? <div aria-hidden="true" /> : <div className="brand-mark-sidebar">Рабочая зона FitFabrica</div>}
          <button
            aria-label={collapsed ? "Развернуть панель" : "Свернуть панель"}
            className="sidebar-item flex h-10 min-w-[4.5rem] shrink-0 items-center justify-center border border-[var(--border)] bg-[var(--background)] px-2 text-[0.8rem] font-semibold text-[var(--text-secondary)] transition hover:bg-black/4 hover:text-black"
            onClick={() => setCollapsed((current) => !current)}
            type="button"
          >
            {collapsed ? ">" : "<"}
          </button>
        </div>

        <div className="mt-4 rounded-[1rem] border border-[var(--border)] bg-[var(--surface)] px-3 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--surface-alt)] text-sm font-semibold">
              {(bootstrap?.user.first_name ?? "Г")[0]}
            </div>
            {collapsed ? null : (
              <div className="min-w-0">
                <p className="truncate text-[0.92rem] font-semibold text-black">
                  {bootstrap?.user.full_name ?? "Гость FitFabrica"}
                </p>
                <p className="truncate text-[0.78rem] text-[var(--text-secondary)]">
                  {bootstrap?.business_profile.exists
                    ? "Единый B2C + B2B кабинет"
                    : "Личные и бизнес-сценарии в одном кабинете"}
                </p>
              </div>
            )}
          </div>
        </div>

        {!collapsed ? (
          <div className="mt-4 min-h-0 flex-1 overflow-y-auto overflow-x-hidden pr-1">
            <a className="workspace-meta inline-flex items-center gap-2 transition hover:text-black" href="/workspace">
              Вернуться к кабинету
            </a>

            <WorkspaceCapabilityCta capability="try_on_create" className="mt-4 w-full" href="/workspace/new-fitting" showReason={false} variant="violet">
              Новая примерка
            </WorkspaceCapabilityCta>

            <div className="mt-5 text-[0.76rem] font-semibold uppercase tracking-[0.18em] text-[var(--text-muted)]">Рабочие разделы</div>

            <nav className="mt-3 flex flex-col gap-1">
              {workspaceRoutes.map((route) => {
                const active = isRouteActive(currentPath, route.href);
                const enabled = !route.capability || (bootstrap?.capabilities.includes(route.capability) ?? false);

                return enabled ? (
                  <a
                    className={`sidebar-item flex items-center px-3 transition ${
                      active
                        ? "bg-[rgba(124,92,255,0.10)] text-[#6D5DF6]"
                        : "text-[var(--text-secondary)] hover:bg-black/4 hover:text-black"
                    }`}
                    href={route.href}
                    key={route.href}
                  >
                    <span className="truncate">{route.label}</span>
                  </a>
                ) : (
                  <button
                    className="sidebar-item flex cursor-not-allowed items-center px-3 text-left text-[var(--text-muted)] opacity-60"
                    disabled
                    key={route.href}
                    title="Раздел временно недоступен для этого workspace."
                    type="button"
                  >
                    <span className="truncate">{route.label}</span>
                  </button>
                );
              })}
            </nav>

            <div className="mt-6 rounded-[1.4rem] border border-[var(--border)] bg-[var(--surface-alt)] p-4">
              <p className="workspace-meta">Интеграция магазина</p>
              <p className="workspace-body mt-3">
                {bootstrap?.integrations.has_connected_store
                  ? "Магазин подключён. Можно расширять сценарии публикации и синхронизации."
                  : "Генерация и ручная выгрузка доступны уже сейчас. Публикация откроется после подключения магазина."}
              </p>
            </div>
          </div>
        ) : (
          <div className="mt-4 flex-1" />
        )}

        <div className="mt-auto pt-4">
          <SiteButton className="w-full" href="/workspace/style-profile" variant="primary">
            {collapsed ? "Профиль" : "Профиль стиля"}
          </SiteButton>
          {!collapsed ? (
            <p className="workspace-meta mt-2">
              Заполните профиль, чтобы будущие рекомендации по стилю и образам были точнее.
            </p>
          ) : null}
        </div>
      </div>
    </aside>
  );
}
