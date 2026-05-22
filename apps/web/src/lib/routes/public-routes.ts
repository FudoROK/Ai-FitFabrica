import type { NavRoute } from "@/types/site";

export const publicRoutes: NavRoute[] = [
  { href: "/for-you", label: "Для себя" },
  { href: "/business", label: "Для бизнеса" },
  { href: "/capabilities", label: "Возможности" },
  { href: "/how-it-works", label: "Как работает" },
  { href: "/pricing", label: "Тарифы" }
];

export const publicFooterRoutes: NavRoute[] = [
  { href: "/privacy", label: "Приватность" },
  { href: "/contacts", label: "Контакты" },
  { href: "/pricing", label: "Условия" }
];
