# AI FitFabrica Web

## Структура

- `src/app` — маршруты Next.js и layout'ы public/workspace
- `src/components` — переиспользуемые navigation и UI-компоненты
- `src/features` — page-level рендереры public и workspace
- `src/lib/content` — контент страниц без смешивания с JSX
- `src/lib/routes` — единая карта навигации
- `src/lib/api` — типизированные контракты интеграции
- `src/types` — общие типы frontend
- `public/site/screens` — все изображения сайта, взятые из `sait/scrin`

## Команды

- `npm install`
- `npm run lint`
- `npm run typecheck`
- `npm run build`
- `npm run dev`
