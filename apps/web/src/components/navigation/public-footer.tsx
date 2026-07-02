import Link from "next/link";
import { publicFooterRoutes } from "@/lib/routes/public-routes";

export function PublicFooter() {
  return (
    <footer className="border-t border-[var(--border)] bg-[var(--background)]">
      <div className="site-container flex flex-col gap-6 py-8 text-sm text-[var(--text-muted)] lg:flex-row lg:items-center lg:justify-between">
        <Link
          aria-label="Go to home page"
          className="brand-mark inline-flex items-center rounded-full text-black transition-transform duration-200 hover:-translate-y-0.5 hover:scale-[1.02] active:scale-[0.97] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-4"
          href="/"
        >
          AI FitFabrica
        </Link>
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
