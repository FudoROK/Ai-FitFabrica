import type { PublicPageContent } from "@/types/site";

export const publicPagesExtra: Record<string, PublicPageContent> = {
  pricing: {
    eyebrow: "Тарифы",
    title: "Простая структура тарифов без визуального мусора",
    lead:
      "Страница тарифов теперь показывает продуманную продуктовую рамку. Финальные цены, лимиты и billing-правила позже подключаются к backend-контрактам.",
    actions: [
      { href: "/contact", label: "Обсудить тариф", variant: "primary" },
      { href: "/workspace/credits", label: "Открыть credits workspace", variant: "secondary" }
    ],
    metrics: [
      { label: "Модель", value: "Подписка + кредиты" },
      { label: "Подходит", value: "Личный и бизнес-сценарий" },
      { label: "Интеграция", value: "Billing подключается отдельно" }
    ],
    highlights: [
      {
        title: "Start",
        body: "Для первых сценариев, тестирования интерфейса и валидации продукта."
      },
      {
        title: "Growth",
        body: "Для регулярной примерки, рабочего каталога и команды, которая создает контент постоянно."
      },
      {
        title: "Enterprise",
        body: "Для брендов с требованиями к SLA, интеграции, ролям и бренд-профилю."
      }
    ],
    steps: [
      {
        title: "Определите сценарий",
        body: "Личный wardrobe flow, регулярный ecommerce контент или операционная работа команды."
      },
      {
        title: "Привяжите лимиты к задаче",
        body: "Частота генераций, объем каталога и число пользователей должны жить в backend-логике."
      },
      {
        title: "Подключите billing позже",
        body: "Финальный прайсинг и оплата не захардкожены в frontend и подставляются после интеграции."
      }
    ],
    placeholder: {
      eyebrow: "Pricing Placeholder",
      title: "Место для живой таблицы тарифов",
      body: "Здесь можно позже разместить pricing grid, калькулятор лимитов или comparison table.",
      items: ["Plan cards", "Limits", "Credits", "CTA"]
    },
    cta: {
      title: "Нужна схема тарификации под бренд",
      body: "Покажите объем каталога и командный контур, чтобы привязать тариф к реальной операционной нагрузке.",
      action: { href: "/contact", label: "Обсудить pricing", variant: "primary" }
    }
  },
  privacy: {
    eyebrow: "Приватность",
    title: "Данные, изображения и результаты должны обрабатываться в управляемом контуре",
    lead:
      "Эта страница оформлена как понятная enterprise-коммуникация: какие данные используются, где проходят проверки и как система должна быть подключена к backend-политикам.",
    actions: [
      { href: "/contact", label: "Запросить security review", variant: "primary" },
      { href: "/workspace/business-profile", label: "Открыть business profile", variant: "secondary" }
    ],
    metrics: [
      { label: "Фокус", value: "Data handling" },
      { label: "Подход", value: "Backend-first" },
      { label: "Контур", value: "Политики и аудит" }
    ],
    highlights: [
      {
        title: "Использование фото",
        body: "Изображения должны участвовать только в тех workflow, которые явно инициирует пользователь или команда."
      },
      {
        title: "Структурированный доступ",
        body: "Секреты, роли, audit trail и жизненный цикл данных не решаются на фронтенде и не должны быть там захардкожены."
      },
      {
        title: "Прозрачные статусы",
        body: "Пользователь должен видеть, что отправлено, что проверяется и что уже доступно в результате."
      }
    ],
    steps: [
      {
        title: "Определите тип данных",
        body: "Фото человека, фото товара, бренд-референсы и generated content должны иметь разную политику хранения."
      },
      {
        title: "Проведите проверку",
        body: "Верификация, удаление, ретеншн и статус ошибок должны приходить из backend."
      },
      {
        title: "Покажите только нужное",
        body: "Frontend отображает статусы и правила понятно, но не хранит чувствительную логику внутри себя."
      }
    ],
    placeholder: {
      eyebrow: "Security Placeholder",
      title: "Блок для схемы data handling",
      body: "Позже сюда можно вставить security diagram, retention table или enterprise trust page visual.",
      items: ["Data flow", "Retention", "Roles", "Audit"]
    },
    cta: {
      title: "Нужна отдельная архитектурная проверка",
      body: "Подготовим требования к хранению данных и внешним интеграциям до production-подключения.",
      action: { href: "/contact", label: "Связаться с командой", variant: "primary" }
    }
  }
};
