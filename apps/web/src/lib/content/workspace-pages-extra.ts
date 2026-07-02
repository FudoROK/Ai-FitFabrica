import type { WorkspacePageContent } from "@/types/site";

export const workspacePagesExtra: Record<string, WorkspacePageContent> = {
  contentPackage: {
    eyebrow: "Content Package",
    title: "Контент-пакет для публикации",
    lead:
      "Экран рассчитан на готовый набор материалов: визуалы, текстовые блоки, AI-заметки и статусы готовности к экспорту.",
    actions: [
      { href: "/workspace/product-card", label: "Вернуться к товару", variant: "primary" },
      { href: "/workspace/history", label: "Сохранить в историю", variant: "secondary" }
    ],
    status: [
      { label: "Состав", value: "Visuals + copy" },
      { label: "Готовность", value: "Needs backend data" },
      { label: "Финал", value: "Export package" }
    ],
    checklist: [
      {
        title: "Визуалы",
        body: "Место для hero-изображения, дополнительных ракурсов и маркетинговых кропов."
      },
      {
        title: "Тексты",
        body: "Описание товара, короткий pitch и служебные заметки команды."
      },
      {
        title: "Экспортные действия",
        body: "Сохранение, публикация и передача в следующий инструмент должны зависеть от backend-статуса."
      }
    ],
    panels: [
      {
        title: "Package overview",
        body: "Собирает все артефакты в одном спокойном продуктовом экране."
      },
      {
        title: "AI notes",
        body: "Показывает рекомендации по стилю, упаковке и качеству без имитации готового результата."
      },
      {
        title: "Export rail",
        body: "Оставляет только нужные действия и убирает визуальную перегрузку."
      }
    ],
    placeholder: {
      eyebrow: "Package Placeholder",
      title: "Будущий контент-пакет",
      body: "Позже сюда можно встроить реальные материалы кампании, карточки и варианты публикации.",
      items: ["Visual set", "Copy set", "Readiness", "Export"]
    }
  },
  styleProfile: {
    eyebrow: "Style Profile",
    title: "Профиль стиля",
    lead:
      "Экран под будущую анкету предпочтений и параметры стиля. Сейчас он собран как enterprise-ready shell без фальшивых картинок.",
    actions: [
      { href: "/workspace/new-fitting", label: "Вернуться к примерке", variant: "primary" },
      { href: "/workspace/outfit-builder", label: "Перейти к образу", variant: "secondary" }
    ],
    status: [
      { label: "Статус", value: "Form-ready" },
      { label: "Источник", value: "User preferences" },
      { label: "Используется", value: "Try-On и outfit builder" }
    ],
    checklist: [
      {
        title: "Предпочтения по посадке",
        body: "Поля для fit preference, comfort level и ключевых ограничений."
      },
      {
        title: "Цвет и стиль",
        body: "Профиль пригоден для подбора палитры, сезонности и роли образа."
      },
      {
        title: "Дальнейшее использование",
        body: "Этот набор данных должен участвовать в следующих AI-сценариях через backend."
      }
    ],
    panels: [
      {
        title: "Preference form",
        body: "Экран подготовлен под форму, а не под декоративный mockup."
      },
      {
        title: "Preview context",
        body: "Пользователь видит, как профиль влияет на следующие сценарии."
      },
      {
        title: "Traceability",
        body: "Backend сможет валидировать, когда и как профиль был обновлен."
      }
    ],
    placeholder: {
      eyebrow: "Profile Placeholder",
      title: "Зона профиля стиля",
      body: "Позже сюда можно встроить реальные формы, селекторы и preview влияния параметров.",
      items: ["Fit preferences", "Color palette", "Use cases", "Save state"]
    }
  },
  businessProfile: {
    eyebrow: "Business Profile",
    title: "Профиль бренда и каналы публикации",
    lead:
      "Рабочий экран для настройки бренда, правил контента и каналов продаж без фальшивого каталожного скрина.",
    actions: [
      { href: "/workspace/product-card", label: "Вернуться к товару", variant: "primary" },
      { href: "/contacts", label: "Обсудить интеграцию", variant: "secondary" }
    ],
    status: [
      { label: "Объект", value: "Brand settings" },
      { label: "Назначение", value: "Unified content output" },
      { label: "Дальше", value: "Connect backend profile" }
    ],
    checklist: [
      {
        title: "Брендовый тон",
        body: "Описание tone of voice, премиальности и допустимой визуальной рамки."
      },
      {
        title: "Каналы публикации",
        body: "Маркетплейсы, собственный сайт, social и внутренние витрины."
      },
      {
        title: "Контентные ограничения",
        body: "Правила по длине текста, форматам изображений и статусам согласования."
      }
    ],
    panels: [
      {
        title: "Profile editor",
        body: "Экран рассчитан на редактирование и контрольный просмотр параметров бренда."
      },
      {
        title: "Operational rules",
        body: "Панель может показывать активные ограничения и AI-режимы для разных каналов."
      },
      {
        title: "Publishing readiness",
        body: "Финальный статус зависит от backend-валидации, а не от фронтенд-декора."
      }
    ],
    placeholder: {
      eyebrow: "Brand Placeholder",
      title: "Панель профиля бренда",
      body: "Позже сюда можно встроить реальные настройки бренда, moodboard и channel presets.",
      items: ["Brand tone", "Channels", "Rules", "Approval"]
    }
  },
  credits: {
    eyebrow: "Credits",
    title: "Баланс и правила списания",
    lead:
      "Экран credits выглядит как системная продуктовая страница, а не как псевдо-скрин со случайными числами.",
    actions: [
      { href: "/pricing", label: "Открыть тарифы", variant: "primary" },
      { href: "/workspace/history", label: "Посмотреть историю", variant: "secondary" }
    ],
    status: [
      { label: "Balance", value: "Backend-driven" },
      { label: "Rules", value: "Usage-based" },
      { label: "UI state", value: "Ready for integration" }
    ],
    checklist: [
      {
        title: "Баланс",
        body: "Показывается как отдельный статусный блок после реального ответа backend."
      },
      {
        title: "Причины списания",
        body: "Каждый workflow может объяснить, за что именно тратятся кредиты."
      },
      {
        title: "No credits state",
        body: "Экран должен спокойно объяснить блокировку и предложить пополнение."
      }
    ],
    panels: [
      {
        title: "Balance panel",
        body: "Готов под числа, лимиты и статусы без захардкоженных значений."
      },
      {
        title: "Usage history",
        body: "История операций остается отдельным блоком и не спорит с основным статусом."
      },
      {
        title: "Top-up flow",
        body: "Подключается после billing-интеграции и живет в отдельном безопасном сценарии."
      }
    ],
    placeholder: {
      eyebrow: "Credits Placeholder",
      title: "Зона баланса и операций",
      body: "Позже сюда можно встроить live balance, usage chart и top-up module.",
      items: ["Balance", "Usage", "No credits", "Top-up CTA"]
    }
  },
  history: {
    eyebrow: "History",
    title: "История запусков и сохраненных результатов",
    lead:
      "Вместо нарисованного списка система теперь имеет продуктовую структуру под реальные записи, фильтры и повторный запуск сценариев.",
    actions: [
      { href: "/workspace/new-fitting", label: "Новый запуск", variant: "primary" },
      { href: "/workspace", label: "Вернуться на главную", variant: "secondary" }
    ],
    status: [
      { label: "Источник", value: "Completed flows" },
      { label: "Функция", value: "Review and reuse" },
      { label: "Режим", value: "History list" }
    ],
    checklist: [
      {
        title: "Список запусков",
        body: "Каждая запись должна показывать тип сценария, дату, статус и доступные действия."
      },
      {
        title: "Повторное использование",
        body: "Пользователь или команда могут открыть результат снова без ручного поиска по папкам."
      },
      {
        title: "Фильтры и сортировка",
        body: "История рассчитана на реальные данные и должна поддерживать типизированные фильтры."
      }
    ],
    panels: [
      {
        title: "History rail",
        body: "Список запусков становится центральным продуктовыми элементом страницы."
      },
      {
        title: "Selected item",
        body: "Рядом можно показать краткий preview и ключевые действия по выбранной записи."
      },
      {
        title: "Operational audit",
        body: "Экран удобно расширять audit-метаданными, когда они появятся на backend."
      }
    ],
    placeholder: {
      eyebrow: "History Placeholder",
      title: "Список сохраненных запусков",
      body: "Позже сюда можно встроить реальную историю, фильтры, quick actions и preview выбранной записи.",
      items: ["Flow list", "Filters", "Preview", "Rerun action"]
    }
  }
};
