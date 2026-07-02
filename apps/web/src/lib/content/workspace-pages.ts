import type { WorkspacePageContent } from "@/types/site";

export const workspacePages: Record<string, WorkspacePageContent> = {
  dashboard: {
    eyebrow: "Workspace",
    title: "Операционный центр FitFabrica",
    lead:
      "Рабочее пространство собрано вокруг активных процессов: примерка, карточки товара, профиль бренда и AI-проверки.",
    actions: [
      { href: "/workspace/new-fitting", label: "Создать новый сценарий", variant: "primary" },
      { href: "/workspace/history", label: "Открыть историю", variant: "secondary" }
    ],
    status: [
      { label: "Активный поток", value: "Try-On" },
      { label: "Готовность", value: "Интерфейс собран" },
      { label: "Следующий шаг", value: "Подключить backend" }
    ],
    checklist: [
      {
        title: "Запустить примерку",
        body: "Подготовьте фото и вещь, затем откройте новый workflow."
      },
      {
        title: "Собрать карточку товара",
        body: "Перейдите в product-card flow, чтобы подготовить основу под ecommerce-контент."
      },
      {
        title: "Настроить бренд",
        body: "Опишите каналы публикации, tone of voice и формат будущих материалов."
      }
    ],
    panels: [
      {
        title: "Состояние продукта",
        body: "Frontend перестроен под реальные панели и формы без декоративных скриншотов."
      },
      {
        title: "Статусы AI",
        body: "Каждый экран показывает понятные проверки качества, загрузки и результата."
      },
      {
        title: "Интеграционный контур",
        body: "Typed API client и формы готовы к подключению backend-эндпоинтов."
      }
    ],
    placeholder: {
      eyebrow: "Workspace Preview",
      title: "Главная продуктовая панель",
      body: "Позже сюда можно встроить live preview результата, историю задач или операционный overview.",
      items: ["Preview area", "Status panel", "Inputs", "Next action"]
    }
  },
  newTryOn: {
    eyebrow: "Try-On Flow",
    title: "Новая примерка",
    lead:
      "Экран подготовки к генерации: загрузка материалов, проверка качества и переход к созданию результата.",
    actions: [
      { href: "/workspace/try-on/result", label: "Перейти к результату", variant: "primary" },
      { href: "/workspace/style-profile", label: "Открыть профиль стиля", variant: "secondary" }
    ],
    status: [
      { label: "Входные данные", value: "Ожидаются" },
      { label: "AI ready", value: "После проверки" },
      { label: "Формат", value: "Фото + товар" }
    ],
    checklist: [
      {
        title: "Фото пользователя",
        body: "Зона загрузки должна принять исходник и проверить базовое качество изображения."
      },
      {
        title: "Фото или ссылка на товар",
        body: "Второй вход нужен для вещи, которую пользователь собирается примерить."
      },
      {
        title: "Проверка перед запуском",
        body: "Frontend показывает статус, а решение о валидности и запуске принимает backend."
      }
    ],
    panels: [
      {
        title: "Upload zone",
        body: "Позже здесь должны появиться управляемые зоны загрузки с прогрессом и ошибками."
      },
      {
        title: "AI quality panel",
        body: "Панель справа показывает пригодность фото, риск по качеству и рекомендации перед запуском."
      },
      {
        title: "Primary action",
        body: "Главное действие остается единым и понятным: пользователь запускает генерацию после проверки."
      }
    ],
    placeholder: {
      eyebrow: "Try-On Placeholder",
      title: "Preview перед генерацией",
      body: "Позже сюда можно встроить live canvas, before/after или контрольную зону результата.",
      items: ["User photo", "Garment photo", "Quality check", "Generate CTA"]
    }
  },
  tryOnResult: {
    eyebrow: "Result Review",
    title: "Результат примерки",
    lead:
      "Экран результата подготовлен для живой выдачи, заметок, качества и перехода к следующему действию.",
    actions: [
      { href: "/workspace/outfit-builder", label: "Подобрать образ", variant: "primary" },
      { href: "/workspace/similar-search", label: "Найти похожее", variant: "secondary" }
    ],
    status: [
      { label: "Статус", value: "Result ready" },
      { label: "Проверка", value: "AI review panel" },
      { label: "Дальше", value: "Save or continue" }
    ],
    checklist: [
      {
        title: "Оценка результата",
        body: "Пользователь видит итоговую выдачу, а не декоративную иллюстрацию."
      },
      {
        title: "Заметки по фасону",
        body: "Панель может показать fit-notes, риск по качеству и рекомендации по стилизации."
      },
      {
        title: "Выбор следующего шага",
        body: "Можно сохранить результат, перейти в outfit builder или искать альтернативу дешевле."
      }
    ],
    panels: [
      {
        title: "Главный preview",
        body: "Центральная зона рассчитана на крупный результат, который доминирует над остальным интерфейсом."
      },
      {
        title: "AI checklist",
        body: "Проверяется цвет, посадка, целостность материала и готовность к сохранению."
      },
      {
        title: "Action rail",
        body: "Ключевые действия вынесены отдельно и не конкурируют друг с другом."
      }
    ],
    placeholder: {
      eyebrow: "Result Placeholder",
      title: "Зона живого результата",
      body: "Позже сюда можно встроить готовый рендер, review mode или comparison с исходником.",
      items: ["Main preview", "Fit notes", "Quality badges", "Save result"]
    }
  },
  outfitBuilder: {
    eyebrow: "Outfit Builder",
    title: "Подбор образа",
    lead:
      "Следующий слой после примерки: собрать комплект, уточнить роль вещи и выбрать направление стилизации.",
    actions: [
      { href: "/workspace/try-on/result", label: "Вернуться к результату", variant: "primary" },
      { href: "/workspace/similar-search", label: "Искать альтернативы", variant: "secondary" }
    ],
    status: [
      { label: "База", value: "Одна ключевая вещь" },
      { label: "Режим", value: "Look composition" },
      { label: "Выход", value: "Набор сочетаний" }
    ],
    checklist: [
      {
        title: "Базовая вещь",
        body: "Определите предмет, вокруг которого строится образ."
      },
      {
        title: "Контекст использования",
        body: "Повседневный, деловой, вечерний или сезонный сценарий должен влиять на рекомендации."
      },
      {
        title: "Готовые комбинации",
        body: "Пользователь получает несколько направлений, а не один произвольный ответ."
      }
    ],
    panels: [
      {
        title: "Look preview",
        body: "Зона визуала рассчитана на комплект, а не на единичный товар."
      },
      {
        title: "Style rules",
        body: "Панель может объяснять, почему AI рекомендует те или иные сочетания."
      },
      {
        title: "Follow-up actions",
        body: "Дальше пользователь сохраняет подборку или ищет похожие позиции."
      }
    ],
    placeholder: {
      eyebrow: "Look Builder Placeholder",
      title: "Зона будущего образа",
      body: "Позже сюда можно встроить outfit board, модуль сочетаний или карточки образов.",
      items: ["Base item", "Layering", "Palette", "Style rationale"]
    }
  },
  similar: {
    eyebrow: "Alternative Search",
    title: "Поиск похожих вариантов",
    lead:
      "Экран подготовлен под реальный список альтернатив, фильтры и backend-поиск, а не под статичный каталог.",
    actions: [
      { href: "/workspace/new-fitting", label: "Начать новый поиск", variant: "primary" },
      { href: "/workspace/history", label: "Открыть историю", variant: "secondary" }
    ],
    status: [
      { label: "Источник", value: "Один референс" },
      { label: "Сортировка", value: "Похожесть / цена" },
      { label: "Результат", value: "Список альтернатив" }
    ],
    checklist: [
      {
        title: "Референсная вещь",
        body: "Система использует исходный товар или результат примерки как опорную точку."
      },
      {
        title: "Фильтры поиска",
        body: "Цена, категория, тональность и сходство подключаются как типизированные параметры."
      },
      {
        title: "Реальные карточки",
        body: "Экран готов под список результатов, ссылки и сохранение в избранное."
      }
    ],
    panels: [
      {
        title: "Result list",
        body: "Вместо декоративного каталога здесь должен жить реальный поток карточек."
      },
      {
        title: "Compare panel",
        body: "Рядом можно показать сходство с исходной вещью и ключевые отличия."
      },
      {
        title: "Price guidance",
        body: "AI-панель объясняет, почему система рекомендует конкретные альтернативы."
      }
    ],
    placeholder: {
      eyebrow: "Search Placeholder",
      title: "Сетка альтернатив",
      body: "Позже сюда можно встроить product cards, фильтры и compare mode.",
      items: ["Filters", "Result cards", "Price notes", "Similarity score"]
    }
  },
  productCard: {
    eyebrow: "Product Workflow",
    title: "Карточка товара",
    lead:
      "Экран подготовлен для сборки карточки товара как продукта: описание, визуал, атрибуты и экспорт.",
    actions: [
      { href: "/workspace/content-package", label: "Открыть контент-пакет", variant: "primary" },
      { href: "/workspace/business-profile", label: "Настроить бренд", variant: "secondary" }
    ],
    status: [
      { label: "SKU", value: "Один товар" },
      { label: "Режим", value: "Content assembly" },
      { label: "Финал", value: "Marketplace-ready output" }
    ],
    checklist: [
      {
        title: "Собрать описание",
        body: "Здесь должны жить title, ключевые характеристики и marketplace-friendly copy."
      },
      {
        title: "Проверить визуал",
        body: "Изображения и варианты подачи должны пройти quality-check перед публикацией."
      },
      {
        title: "Подготовить экспорт",
        body: "Финальный артефакт должен быть готов к публикации или передаче в контент-пакет."
      }
    ],
    panels: [
      {
        title: "Content editor",
        body: "Экран рассчитан на рабочее редактирование, а не на статичную витрину."
      },
      {
        title: "AI notes",
        body: "Панель справа показывает рекомендации по карточке, цене и качеству материалов."
      },
      {
        title: "Publishing rail",
        body: "Экспорт и следующие действия живут в отдельном безопасном контуре."
      }
    ],
    placeholder: {
      eyebrow: "Product Placeholder",
      title: "Зона карточки товара",
      body: "Позже сюда можно встроить реальную карточку, атрибуты, preview и publish actions.",
      items: ["Description", "Attributes", "Preview", "Export"]
    }
  }
};
