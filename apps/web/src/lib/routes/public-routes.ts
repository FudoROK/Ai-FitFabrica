import type { NavRoute } from "@/types/site";

export const publicRoutes: NavRoute[] = [
  { href: "/for-you", label: "Для себя" },
  { href: "/business", label: "Для бизнеса" },
  { href: "/features", label: "Возможности" },
  { href: "/how-it-works", label: "Как работает" },
  { href: "/pricing", label: "Тарифы" }
];

export const publicFooterRoutes: NavRoute[] = [
  { href: "/about", label: "О платформе" },
  { href: "/privacy", label: "Приватность" },
  { href: "/contact", label: "Контакты" },
  { href: "/pricing", label: "Условия" }
];
