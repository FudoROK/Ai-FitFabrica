export type WorkspaceRoute = {
  href: string;
  label: string;
  icon: string;
};

export const workspaceRoutes: WorkspaceRoute[] = [
  { href: "/workspace", label: "Кабинет", icon: "dashboard" },
  { href: "/workspace/try-on/new", label: "Новая примерка", icon: "add_a_photo" },
  { href: "/workspace/outfit-builder", label: "Подбор образа", icon: "auto_fix_high" },
  { href: "/workspace/similar", label: "Найти похожее", icon: "search" },
  { href: "/workspace/product-card", label: "Карточка товара", icon: "shopping_bag" },
  { href: "/workspace/history", label: "История", icon: "history" },
  { href: "/workspace/credits", label: "Кредиты", icon: "payments" },
  { href: "/workspace/style-profile", label: "Профиль стиля", icon: "person" },
  { href: "/workspace/business-profile", label: "Профиль бизнеса", icon: "business_center" }
];
