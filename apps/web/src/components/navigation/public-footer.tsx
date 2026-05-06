import Link from "next/link";
import { publicFooterRoutes } from "@/lib/routes/public-routes";

export function PublicFooter() {
  return (
    <footer className="site-footer">
      <div className="page-shell site-footer-shell">
        <div>
          <strong className="site-logo">AI FitFabrica</strong>
          <p className="site-footer-copy">
            Спокойный product-first интерфейс для примерки, контент-пакетов и fashion-операций.
          </p>
        </div>
        <nav className="site-footer-nav">
          {publicFooterRoutes.map((route) => (
            <Link key={route.href} href={route.href}>
              {route.label}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  );
}
