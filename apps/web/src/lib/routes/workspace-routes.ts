import type { NavRoute } from "@/types/site";

export const workspaceRoutes: NavRoute[] = [
  { href: "/workspace", label: "Обзор" },
  { href: "/workspace/try-on/new", label: "Новая примерка" },
  { href: "/workspace/try-on/result", label: "Результат примерки" },
  { href: "/workspace/outfit-builder", label: "Подбор образа" },
  { href: "/workspace/similar", label: "Похожие товары" },
  { href: "/workspace/product-card", label: "Карточка товара" },
  { href: "/workspace/content-package", label: "Контент-пакет" },
  { href: "/workspace/style-profile", label: "Профиль стиля" },
  { href: "/workspace/business-profile", label: "Профиль бренда" },
  { href: "/workspace/credits", label: "Кредиты" },
  { href: "/workspace/history", label: "История" }
];
