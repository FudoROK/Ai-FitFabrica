"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { publicRoutes } from "@/lib/routes/public-routes";

export function PublicHeader() {
  const pathname = usePathname();

  return (
    <header className="site-header">
      <div className="page-shell site-header-shell">
        <Link className="site-logo" href="/">
          AI FitFabrica
        </Link>
        <nav className="site-nav">
          {publicRoutes.map((route) => (
            <Link
              className={pathname === route.href ? "site-nav-link site-nav-link-active" : "site-nav-link"}
              key={route.href}
              href={route.href}
            >
              {route.label}
            </Link>
          ))}
        </nav>
        <div className="site-header-actions">
          <Link className="site-header-link" href="/sign-in">
            Войти
          </Link>
          <Link className="button button-primary" href="/workspace/try-on/new">
            Начать примерку
          </Link>
        </div>
      </div>
    </header>
  );
}
