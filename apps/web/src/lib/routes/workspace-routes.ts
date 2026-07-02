import type { WorkspaceCapability } from "@/lib/api/contracts";

export type WorkspaceRoute = {
  capability?: WorkspaceCapability;
  href: string;
  icon: string;
  label: string;
};

export const workspaceRoutes: WorkspaceRoute[] = [
  { href: "/workspace", label: "Кабинет", icon: "dashboard" },
  { href: "/workspace/new-fitting", label: "Новая примерка", icon: "add_a_photo", capability: "try_on_create" },
  { href: "/workspace/outfit-builder", label: "Подбор образа", icon: "auto_fix_high", capability: "outfit_builder_create" },
  { href: "/workspace/similar-search", label: "Найти похожее", icon: "search", capability: "similar_search_create" },
  { href: "/workspace/product-card", label: "Карточка товара", icon: "shopping_bag", capability: "product_card_create" },
  { href: "/workspace/business-catalog", label: "Каталог товаров", icon: "inventory" },
  { href: "/workspace/projects", label: "Проекты", icon: "inventory_2" },
  { href: "/workspace/credits", label: "Кредиты", icon: "payments" },
  { href: "/workspace/settings", label: "Настройки", icon: "tune" },
];
