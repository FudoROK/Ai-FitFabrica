"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { publicRoutes } from "@/lib/routes/public-routes";
import { SiteButton } from "@/components/site/site-button";

export function PublicHeader() {
  const pathname = usePathname();
  const isSignIn = pathname === "/sign-in";

  return (
    <header className="border-b border-[var(--border)] bg-[var(--background)]">
      <div className="site-container flex min-h-[82px] items-center justify-between gap-8">
        <Link className="font-[family-name:var(--font-manrope)] text-[2.1rem] font-bold tracking-[-0.04em]" href="/">
          AI FitFabrica
        </Link>
        <nav className="hidden items-center gap-8 lg:flex">
          {publicRoutes.map((route) => {
            const active = pathname === route.href;

            return (
              <Link
                className={`border-b-2 pb-1 text-sm font-medium transition ${active ? "border-black text-black" : "border-transparent text-[var(--text-secondary)] hover:text-black"}`}
                href={route.href}
                key={route.href}
              >
                {route.label}
              </Link>
            );
          })}
        </nav>
        <div className="hidden items-center gap-4 lg:flex">
          <Link className={`text-sm font-semibold ${pathname === "/sign-in" ? "text-black" : "text-[var(--text-secondary)]"}`} href="/sign-in">
            Войти
          </Link>
          <SiteButton href="/workspace/try-on/new" variant={isSignIn ? "secondary" : "primary"}>
            Начать примерку
          </SiteButton>
        </div>
      </div>
    </header>
  );
}
