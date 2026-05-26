import type { WorkspacePageContent } from "@/types/site";

export const workspacePages: Record<string, WorkspacePageContent> = {
  dashboard: {
    eyebrow: "Workspace",
    title: "Операционный центр FitFabrica",
    lead:
      "Рабочее пространство собрано вокруг активных процессов: примерка, карточки товара, brand profile и AI-проверки.",
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
        body: "Подготовьте фото и предмет одежды, затем запустите новый workflow."
      },
      {
        title: "Собрать карточку товара",
        body: "Перейдите в product-card flow, чтобы подготовить структуру под ecommerce-контент."
      },
      {
        title: "Настроить бренд",
        body: "Опишите каналы публикации, tone of voice и формат будущих материалов."
      }
    ],
    panels: [
      {
        title: "Состояние продукта",
        body: "Frontend перестроен под реальные панели и формы. Скриншоты выведены из основного потока."
      },
      {
        title: "Статусы AI",
        body: "Каждый следующий экран рассчитан на понятные проверки качества, загрузки и результата."
      },
      {
        title: "Интеграционный контур",
        body: "Typed API client и формы готовы к подключению backend-эндпоинтов."
      }
    ],
    placeholder: {
      eyebrow: "Workspace Preview",
      title: "Главная продуктовая панель",
      body: "Здесь позже можно показать реальный live preview результата, историю, канбан задач или enterprise overview.",
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
        body: "Вторая зона нужна для вещи, которую пользователь собирается примерить."
      },
      {
        title: "Проверка перед запуском",
        body: "Frontend показывает только статус, а решение о запуске и валидации принимает backend."
      }
    ],
    panels: [
      {
        title: "Upload zone",
        body: "На этом экране позже должны появиться две управляемые зоны загрузки с прогрессом и ошибками."
      },
      {
        title: "AI quality panel",
        body: "Панель справа будет показывать пригодность фото, риск по качеству и рекомендации перед запуском."
      },
      {
        title: "Primary action",
        body: "Главное действие остается единым и понятным: пользователь запускает генерацию после проверки."
      }
    ],
    placeholder: {
      eyebrow: "Try-On Placeholder",
      title: "Заглушка для preview перед генерацией",
      body: "Позже сюда можно вставить live canvas, before/after или контрольную зону результата.",
      items: ["User photo", "Garment photo", "Quality check", "Generate CTA"]
    }
  },
  tryOnResult: {
    eyebrow: "Result Review",
    title: "Результат примерки",
    lead:
      "Экран результата больше не притворяется скриншотом. Он подготовлен для живой выдачи, заметок и следующего действия.",
    actions: [
      { href: "/workspace/outfit-builder", label: "Подобрать образ", variant: "primary" },
      { href: "/workspace/similar", label: "Найти похожее", variant: "secondary" }
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
        body: "Сохранить, перейти в outfit builder или искать альтернативу дешевле."
      }
    ],
    panels: [
      {
        title: "Главный preview",
        body: "Центральная зона рассчитана на крупный результат, который доминирует над остальным интерфейсом."
      },
      {
        title: "AI checklist",
        body: "Проверка цвета, посадки, целостности материала и готовности к сохранению."
      },
      {
        title: "Action rail",
        body: "Важные действия вынесены отдельно и не конкурируют друг с другом."
      }
    ],
    placeholder: {
      eyebrow: "Result Placeholder",
      title: "Зона живого результата",
      body: "Позже сюда можно вставить готовый рендер, review mode или comparison с исходником.",
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
      { href: "/workspace/similar", label: "Искать альтернативы", variant: "secondary" }
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
        body: "Панель может показывать, почему AI рекомендует те или иные сочетания."
      },
      {
        title: "Follow-up actions",
        body: "Дальше пользователь сохраняет подборку или ищет похожие позиции."
      }
    ],
    placeholder: {
      eyebrow: "Look Builder Placeholder",
      title: "Зона будущего образа",
      body: "Позже сюда можно вставить outfit board, модуль сочетаний или карточки образов.",
      items: ["Base item", "Layering", "Palette", "Style rationale"]
    }
  },
  similar: {
    eyebrow: "Alternative Search",
    title: "Поиск похожих вариантов",
    lead:
      "Этот экран больше не изображает каталог через скрин. Он подготовлен под реальный список альтернатив и фильтры backend-поиска.",
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
        body: "Система должна использовать исходный товар или результат примерки как опорную точку."
      },
      {
        title: "Фильтры поиска",
        body: "Цена, категория, тональность и сходство подключаются как typed параметры запроса."
      },
      {
        title: "Реальные карточки",
        body: "Экран готов под список результатов, ссылки и сохранение в избранное."
      }
    ],
    panels: [
      {
        title: "Result list",
        body: "Вместо изображения каталога здесь будет реальный поток карточек."
      },
      {
        title: "Compare panel",
        body: "Рядом можно показать сходство с исходной вещью и ключевые отличия."
      },
      {
        title: "Price guidance",
        body: "AI-панель может объяснить, почему система рекомендует конкретные альтернативы."
      }
    ],
    placeholder: {
      eyebrow: "Search Placeholder",
      title: "Сетка альтернатив",
      body: "Позже сюда можно вставить реальные product cards, фильтры и compare mode.",
      items: ["Filters", "Result cards", "Price notes", "Similarity score"]
    }
  },
  productCard: {
    eyebrow: "Product Workflow",
    title: "Карточка товара",
    lead:
      "Экран подготовлен для карточки товара как продукта, а не как картинки. Здесь должна жить структура под описание, визуал и экспорт.",
    actions: [
      { href: "/workspace/content-package", label: "Открыть контент-пакет", variant: "primary" },
      { href: "/workspace/business-profile", label: "Настроить бренд", variant: "secondary" }
    ],
    status: [
      { label: "SKU", value: "Один товар" },
      { label: "Режим", value: "Content assembly" },
      { label: "Выход", value: "Card + package" }
    ],
    checklist: [
      {
        title: "Описание товара",
        body: "Карточка должна принимать structured fields и текстовые характеристики."
      },
      {
        title: "Визуальные материалы",
        body: "Основной preview и дополнительные материалы появляются в крупной центральной зоне."
      },
      {
        title: "Экспорт",
        body: "Следующие действия: сохранить, отправить в content package или экспортировать."
      }
    ],
    panels: [
      {
        title: "Card structure",
        body: "Панель рассчитана на SKU, описание, преимущества и статусы проверки."
      },
      {
        title: "AI support",
        body: "AI-слой может подсказать тон описания, риск по качеству и readiness к публикации."
      },
      {
        title: "Operational handoff",
        body: "Карточка товара становится частью следующего workflow, а не тупиковой страницей."
      }
    ],
    placeholder: {
      eyebrow: "Product Card Placeholder",
      title: "Место для реальной карточки товара",
      body: "Позже сюда можно вставить SKU-preview, ключевой визуал, описание и метаданные.",
      items: ["SKU info", "Primary visual", "Copy block", "Export actions"]
    }
  }
};
