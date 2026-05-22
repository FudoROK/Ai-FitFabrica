import Link from "next/link";
import { publicFooterRoutes } from "@/lib/routes/public-routes";

export function PublicFooter() {
  return (
    <footer className="border-t border-[var(--border)] bg-[var(--background)]">
      <div className="site-container flex flex-col gap-6 py-8 text-sm text-[var(--text-muted)] lg:flex-row lg:items-center lg:justify-between">
        <strong className="font-[family-name:var(--font-manrope)] text-[2rem] font-bold text-black tracking-[-0.04em]">
          AI FitFabrica
        </strong>
        <p>© 2024 AI FitFabrica. Все права защищены.</p>
        <nav className="flex flex-wrap items-center gap-6">
          {publicFooterRoutes.map((route) => (
            <Link className="transition hover:text-black" href={route.href} key={route.href}>
              {route.label}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  );
}
