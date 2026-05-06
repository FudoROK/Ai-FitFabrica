module.exports = [
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
"[project]/src/components/ui/button-link.tsx [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "ButtonLink",
    ()=>ButtonLink
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-jsx-dev-runtime.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$react$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/client/app-dir/link.react-server.js [app-rsc] (ecmascript)");
;
;
function ButtonLink({ action }) {
    const isPrimary = action.variant !== "secondary";
    const className = isPrimary ? "inline-flex items-center justify-center rounded-full bg-[var(--text-primary)] px-6 py-3 text-sm font-semibold text-white transition hover:opacity-90" : "inline-flex items-center justify-center rounded-full border border-[var(--border)] bg-white/70 px-6 py-3 text-sm font-semibold text-[var(--text-primary)] transition hover:bg-[var(--surface-alt)]";
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$react$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["default"], {
        className: className,
        href: action.href,
        children: action.label
    }, void 0, false, {
        fileName: "[project]/src/components/ui/button-link.tsx",
        lineNumber: 15,
        columnNumber: 5
    }, this);
}
}),
"[project]/src/components/ui/screenshot-frame.tsx [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "ScreenshotFrame",
    ()=>ScreenshotFrame
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-jsx-dev-runtime.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$image$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/image.js [app-rsc] (ecmascript)");
;
;
function ScreenshotFrame({ alt, src }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "surface-card overflow-hidden p-3 shadow-[0_20px_60px_rgba(20,20,20,0.08)]",
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$image$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["default"], {
            alt: alt,
            className: "h-auto w-full rounded-[20px]",
            height: 900,
            priority: true,
            src: src,
            width: 1440
        }, void 0, false, {
            fileName: "[project]/src/components/ui/screenshot-frame.tsx",
            lineNumber: 14,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/src/components/ui/screenshot-frame.tsx",
        lineNumber: 13,
        columnNumber: 5
    }, this);
}
}),
"[project]/src/features/public/public-page.tsx [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "PublicPage",
    ()=>PublicPage
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-jsx-dev-runtime.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$ui$2f$button$2d$link$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/ui/button-link.tsx [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$ui$2f$screenshot$2d$frame$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/components/ui/screenshot-frame.tsx [app-rsc] (ecmascript)");
;
;
;
function PublicPage({ content }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("main", {
        className: "py-10",
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "page-shell space-y-10 pb-16 pt-8",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                    className: "grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "space-y-6",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                    className: "eyebrow",
                                    children: "AI FitFabrica"
                                }, void 0, false, {
                                    fileName: "[project]/src/features/public/public-page.tsx",
                                    lineNumber: 15,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                                    className: "hero-title",
                                    children: content.title
                                }, void 0, false, {
                                    fileName: "[project]/src/features/public/public-page.tsx",
                                    lineNumber: 16,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                    className: "hero-lead",
                                    children: content.lead
                                }, void 0, false, {
                                    fileName: "[project]/src/features/public/public-page.tsx",
                                    lineNumber: 17,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "flex flex-wrap gap-3",
                                    children: content.actions.map((action)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$ui$2f$button$2d$link$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["ButtonLink"], {
                                            action: action
                                        }, `${content.title}-${action.href}-${action.label}`, false, {
                                            fileName: "[project]/src/features/public/public-page.tsx",
                                            lineNumber: 20,
                                            columnNumber: 17
                                        }, this))
                                }, void 0, false, {
                                    fileName: "[project]/src/features/public/public-page.tsx",
                                    lineNumber: 18,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/features/public/public-page.tsx",
                            lineNumber: 14,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$components$2f$ui$2f$screenshot$2d$frame$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["ScreenshotFrame"], {
                            alt: content.title,
                            src: content.image
                        }, void 0, false, {
                            fileName: "[project]/src/features/public/public-page.tsx",
                            lineNumber: 24,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/src/features/public/public-page.tsx",
                    lineNumber: 13,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                    className: "section-grid",
                    children: content.sections.map((section)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("article", {
                            className: "surface-card p-6",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                                    className: "font-[var(--font-manrope)] text-2xl font-bold",
                                    children: section.title
                                }, void 0, false, {
                                    fileName: "[project]/src/features/public/public-page.tsx",
                                    lineNumber: 29,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                    className: "mt-3 text-base leading-7 text-[var(--text-secondary)]",
                                    children: section.body
                                }, void 0, false, {
                                    fileName: "[project]/src/features/public/public-page.tsx",
                                    lineNumber: 30,
                                    columnNumber: 15
                                }, this)
                            ]
                        }, `${content.title}-${section.title}`, true, {
                            fileName: "[project]/src/features/public/public-page.tsx",
                            lineNumber: 28,
                            columnNumber: 13
                        }, this))
                }, void 0, false, {
                    fileName: "[project]/src/features/public/public-page.tsx",
                    lineNumber: 26,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/src/features/public/public-page.tsx",
            lineNumber: 12,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/src/features/public/public-page.tsx",
        lineNumber: 11,
        columnNumber: 5
    }, this);
}
}),
"[project]/src/lib/content/public-pages.ts [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "publicPages",
    ()=>publicPages
]);
const publicPages = {
    home: {
        eyebrow: "AI FitFabrica",
        title: "Платформа для примерки, контента и fashion-операций",
        lead: "FitFabrica помогает брендам и покупателям быстро проверять образы, собирать контент-пакеты и принимать решения без визуального шума и хаоса в процессе.",
        actions: [
            {
                href: "/workspace/try-on/new",
                label: "Начать примерку",
                variant: "primary"
            },
            {
                href: "/business",
                label: "Для бизнеса",
                variant: "secondary"
            }
        ],
        metrics: [
            {
                label: "Сценарии",
                value: "3 продуктовых потока"
            },
            {
                label: "Фокус",
                value: "Контент, примерка, продажи"
            },
            {
                label: "Формат",
                value: "B2C + B2B workspace"
            }
        ],
        highlights: [
            {
                title: "Примерка до покупки",
                body: "Пользователь загружает фото, получает аккуратный результат и понимает, подходит ли фасон, цвет и силуэт."
            },
            {
                title: "Контент для карточек товара",
                body: "Бренд собирает визуалы, описания и AI-рекомендации в одной цепочке без ручной пересборки."
            },
            {
                title: "Чистый продуктовый интерфейс",
                body: "Без скриншотов и псевдо-дашбордов. Только понятные экраны, статусы, формы и сценарии следующего шага."
            }
        ],
        steps: [
            {
                title: "Загрузите исходники",
                body: "Фото человека, предмета одежды или каталожный референс попадают в управляемый workflow."
            },
            {
                title: "AI готовит результат",
                body: "Платформа проверяет качество, собирает задачу и возвращает структурированный результат для следующего действия."
            },
            {
                title: "Продолжайте в workspace",
                body: "Сохраните результат, соберите образ, подготовьте карточку товара или отправьте контент на публикацию."
            }
        ],
        placeholder: {
            eyebrow: "Hero Placeholder",
            title: "Главный визуал продукта",
            body: "Эта панель заменяет временные скриншоты. Позже сюда можно вставить hero-рендер, before/after или живой preview продукта.",
            items: [
                "Hero visual",
                "Before / After",
                "AI status",
                "Primary CTA"
            ]
        },
        cta: {
            title: "Соберите первый сценарий без пересъемки",
            body: "Запустите примерку или обсудите подключение FitFabrica для каталога и контент-команды.",
            action: {
                href: "/contacts",
                label: "Запросить демонстрацию",
                variant: "primary"
            }
        }
    },
    forYou: {
        eyebrow: "Для себя",
        title: "Проверьте образ до покупки и найдите следующий шаг",
        lead: "Пользовательский поток FitFabrica помогает понять, как вещь выглядит на вас, что к ней подойдет и стоит ли искать альтернативу.",
        actions: [
            {
                href: "/workspace/try-on/new",
                label: "Загрузить фото",
                variant: "primary"
            },
            {
                href: "/workspace/similar",
                label: "Найти похожее дешевле",
                variant: "secondary"
            }
        ],
        metrics: [
            {
                label: "Вход",
                value: "Фото + товар"
            },
            {
                label: "Выход",
                value: "Результат + рекомендации"
            },
            {
                label: "Фокус",
                value: "Понятное решение перед покупкой"
            }
        ],
        highlights: [
            {
                title: "Виртуальная примерка",
                body: "Показывает, как вещь работает на силуэте, а не просто выдает декоративную генерацию."
            },
            {
                title: "Стилизация после результата",
                body: "После примерки можно сразу перейти к подбору образа и рекомендациям по сочетаниям."
            },
            {
                title: "Поиск альтернатив",
                body: "Если вещь не подходит по цене или посадке, пользователь двигается дальше без потери контекста."
            }
        ],
        steps: [
            {
                title: "Подготовьте фото",
                body: "Подойдет спокойный кадр в полный рост или поясной портрет с читаемой фигурой."
            },
            {
                title: "Добавьте товар",
                body: "Укажите ссылку, загрузите фото вещи или вставьте вырезку из каталога."
            },
            {
                title: "Оцените результат",
                body: "Система покажет статус, качество, рекомендации по фасону и возможные следующие действия."
            }
        ],
        placeholder: {
            eyebrow: "Preview Placeholder",
            title: "Зона результата для B2C",
            body: "Позже сюда можно вставить реальный пример preview примерки, без изменения структуры страницы.",
            items: [
                "Result preview",
                "Style notes",
                "Quality check",
                "Save action"
            ]
        },
        cta: {
            title: "Начните с одной вещи",
            body: "Один аккуратный сценарий полезнее длинной витрины функций.",
            action: {
                href: "/workspace/try-on/new",
                label: "Открыть примерку",
                variant: "primary"
            }
        }
    },
    business: {
        eyebrow: "Для бизнеса",
        title: "Соберите контент-процесс для fashion-команды без хаотичных ручных этапов",
        lead: "FitFabrica объединяет подготовку визуала, описание товара, рекомендации по стилю и статусы качества в едином рабочем контуре.",
        actions: [
            {
                href: "/contacts",
                label: "Запросить демо",
                variant: "primary"
            },
            {
                href: "/workspace/product-card",
                label: "Открыть product workflow",
                variant: "secondary"
            }
        ],
        metrics: [
            {
                label: "Подходит",
                value: "Для брендов и маркетплейсов"
            },
            {
                label: "Задачи",
                value: "Карточки, пакеты, рекомендации"
            },
            {
                label: "Режим",
                value: "Операционный workspace"
            }
        ],
        highlights: [
            {
                title: "Контент-пакет из одного источника",
                body: "Фотография товара, описание, рекомендации по цене и готовые материалы собираются в управляемую выдачу."
            },
            {
                title: "Спокойный рабочий интерфейс",
                body: "Без кричащих AI-эффектов. У команды перед глазами только текущий статус, входные данные и следующий шаг."
            },
            {
                title: "Подготовка к интеграции",
                body: "Архитектура уже разведена на typed API client и workspace-страницы для дальнейшей backend-интеграции."
            }
        ],
        steps: [
            {
                title: "Опишите каталог",
                body: "Определите ассортимент, каналы публикации и нужные типы контента."
            },
            {
                title: "Настройте стиль выдачи",
                body: "Система использует единый визуальный и операционный подход для всего бренда."
            },
            {
                title: "Получите готовые артефакты",
                body: "Команда работает с карточками, пакетами контента и AI-подсказками без пересборки в сторонних инструментах."
            }
        ],
        placeholder: {
            eyebrow: "B2B Placeholder",
            title: "Зона product / content preview",
            body: "Вместо скрина сюда позже можно вставить пример карточки товара, витрину пакета контента или before/after для каталога.",
            items: [
                "Catalog visual",
                "Content package",
                "AI checks",
                "Export state"
            ]
        },
        cta: {
            title: "Покажите ваш текущий контент-процесс",
            body: "Мы сможем собрать более точный enterprise-поток под бренд, каналы продаж и объем каталога.",
            action: {
                href: "/contacts",
                label: "Обсудить внедрение",
                variant: "primary"
            }
        }
    },
    capabilities: {
        eyebrow: "Возможности",
        title: "Три продуктовых направления, собранные в одну систему",
        lead: "Публичный сайт теперь показывает не набор картинок, а структуру платформы: примерка, product content и AI-операции.",
        actions: [
            {
                href: "/workspace",
                label: "Открыть workspace",
                variant: "primary"
            },
            {
                href: "/how-it-works",
                label: "Посмотреть flow",
                variant: "secondary"
            }
        ],
        metrics: [
            {
                label: "B2C",
                value: "Примерка и стиль"
            },
            {
                label: "B2B",
                value: "Контент и карточки"
            },
            {
                label: "AI",
                value: "Проверки и рекомендации"
            }
        ],
        highlights: [
            {
                title: "Try-On workflow",
                body: "Подготовка исходников, генерация результата и последовательный переход к рекомендациям."
            },
            {
                title: "Product workflow",
                body: "Карточка товара, пакет контента и AI-подсказки собираются вокруг одного SKU."
            },
            {
                title: "Business profile",
                body: "Настройки бренда, каналы публикации и правила выдачи живут в отдельном контуре workspace."
            }
        ],
        steps: [
            {
                title: "Выберите сценарий",
                body: "Личный гардероб, карточка товара или контент-команда."
            },
            {
                title: "Загрузите вводные",
                body: "Система принимает только нужные данные для текущего сценария."
            },
            {
                title: "Двигайтесь по этапам",
                body: "Каждый экран подсказывает следующий шаг: сохранить, продолжить, экспортировать или отправить в работу."
            }
        ],
        placeholder: {
            eyebrow: "System Placeholder",
            title: "Схема возможностей продукта",
            body: "Эта панель может быть заменена позже на интерактивную схему или продуктовый рендер.",
            items: [
                "Try-On",
                "Catalog",
                "AI panel",
                "Brand profile"
            ]
        },
        cta: {
            title: "Откройте систему в рабочем режиме",
            body: "Workspace уже перестроен под реальные панели и дальнейшую backend-интеграцию.",
            action: {
                href: "/workspace",
                label: "Перейти в workspace",
                variant: "primary"
            }
        }
    },
    howItWorks: {
        eyebrow: "Как это работает",
        title: "Поток выстроен вокруг результата, а не вокруг декоративных экранов",
        lead: "FitFabrica ведет пользователя от входных данных к результату через короткие, понятные этапы с проверками и следующими действиями.",
        actions: [
            {
                href: "/workspace/try-on/new",
                label: "Открыть новый сценарий",
                variant: "primary"
            },
            {
                href: "/contacts",
                label: "Нужна консультация",
                variant: "secondary"
            }
        ],
        metrics: [
            {
                label: "Шаг 1",
                value: "Вводные"
            },
            {
                label: "Шаг 2",
                value: "AI обработка"
            },
            {
                label: "Шаг 3",
                value: "Результат и действия"
            }
        ],
        highlights: [
            {
                title: "Одна секция = одна идея",
                body: "Сайт следует design system из `sait`: крупные блоки, один смысл и минимум лишних визуальных слоев."
            },
            {
                title: "Проверяем качество",
                body: "Каждый workflow имеет понятный AI/status слой вместо декоративных подпунктов и шумных карточек."
            },
            {
                title: "Следующий шаг очевиден",
                body: "После любого результата пользователь понимает, что делать дальше: сохранить, продолжить, пересобрать или экспортировать."
            }
        ],
        steps: [
            {
                title: "Соберите задачу",
                body: "Пользователь выбирает тип сценария и загружает ровно те материалы, которые нужны для него."
            },
            {
                title: "Пройдите проверку",
                body: "Система показывает качество входа, статус генерации и важные замечания без скрытых состояний."
            },
            {
                title: "Используйте результат",
                body: "Результат становится частью следующего действия, а не тупиком на красивом экране."
            }
        ],
        placeholder: {
            eyebrow: "Flow Placeholder",
            title: "Диаграмма процесса",
            body: "Позже сюда можно вставить реальную схему flow или анимированный product tour.",
            items: [
                "Input",
                "AI status",
                "Review",
                "Next action"
            ]
        },
        cta: {
            title: "Проверьте flow внутри workspace",
            body: "Рабочие страницы уже перестроены так, чтобы показывать ход процесса, а не скриншоты.",
            action: {
                href: "/workspace/try-on/new",
                label: "Запустить flow",
                variant: "primary"
            }
        }
    }
};
}),
"[project]/src/app/(public)/page.tsx [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>HomePage
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-jsx-dev-runtime.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$features$2f$public$2f$public$2d$page$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/features/public/public-page.tsx [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$content$2f$public$2d$pages$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/content/public-pages.ts [app-rsc] (ecmascript)");
;
;
;
function HomePage() {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$features$2f$public$2f$public$2d$page$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["PublicPage"], {
        content: __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$content$2f$public$2d$pages$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["publicPages"].home
    }, void 0, false, {
        fileName: "[project]/src/app/(public)/page.tsx",
        lineNumber: 5,
        columnNumber: 10
    }, this);
}
}),
"[project]/src/app/(public)/page.tsx [app-rsc] (ecmascript, Next.js Server Component)", ((__turbopack_context__) => {

__turbopack_context__.n(__turbopack_context__.i("[project]/src/app/(public)/page.tsx [app-rsc] (ecmascript)"));
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__087vrp4._.js.map