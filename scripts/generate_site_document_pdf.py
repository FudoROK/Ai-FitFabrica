"""Generate a PDF document with the AI FitFabrica site map and page catalog."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

from site_document_data import FILE_GROUPS, PAGES

PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)
MARGIN = 42
BG = colors.HexColor("#F7F3EC")
PANEL = colors.HexColor("#FFFDF8")
BORDER = colors.HexColor("#DED6CB")
TEXT = colors.HexColor("#181614")
MUTED = colors.HexColor("#675F57")
AI = colors.HexColor("#6E56CF")
BEIGE = colors.HexColor("#D8C3A5")
GREEN = colors.HexColor("#2F8F6B")


def register_fonts() -> None:
    """Register Cyrillic-capable fonts from the local Windows installation."""

    pdfmetrics.registerFont(TTFont("Body", r"C:\Windows\Fonts\arial.ttf"))
    pdfmetrics.registerFont(TTFont("BodyBold", r"C:\Windows\Fonts\arialbd.ttf"))


def make_styles() -> dict[str, ParagraphStyle]:
    """Create reusable paragraph styles for the PDF."""

    sample = getSampleStyleSheet()
    return {
        "body": ParagraphStyle("Body", parent=sample["BodyText"], fontName="Body", fontSize=10.2, leading=13, textColor=TEXT),
        "small": ParagraphStyle("Small", parent=sample["BodyText"], fontName="Body", fontSize=8.6, leading=11, textColor=MUTED),
        "h1": ParagraphStyle("H1", parent=sample["Heading1"], fontName="BodyBold", fontSize=23, leading=26, textColor=TEXT),
        "h2": ParagraphStyle("H2", parent=sample["Heading2"], fontName="BodyBold", fontSize=14, leading=17, textColor=TEXT),
        "tag": ParagraphStyle("Tag", parent=sample["BodyText"], fontName="BodyBold", fontSize=8.8, leading=10, textColor=AI),
    }


def draw_page_background(pdf: Canvas) -> None:
    """Paint the page background."""

    pdf.setFillColor(BG)
    pdf.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)


def draw_panel(pdf: Canvas, x: float, y: float, w: float, h: float, fill: colors.Color = PANEL) -> None:
    """Draw a rounded information panel."""

    pdf.setFillColor(fill)
    pdf.setStrokeColor(BORDER)
    pdf.roundRect(x, y, w, h, 16, fill=1, stroke=1)


def draw_paragraph(pdf: Canvas, text: str, style: ParagraphStyle, x: float, y: float, w: float, h: float) -> None:
    """Render a paragraph into a bounding box."""

    paragraph = Paragraph(text, style)
    _, height = paragraph.wrap(w, h)
    paragraph.drawOn(pdf, x, y - height)


def draw_bullets(pdf: Canvas, items: list[str], x: float, top: float, w: float, style: ParagraphStyle, gap: float = 4) -> float:
    """Render a simple flat bullet list and return the new y position."""

    current_y = top
    for item in items:
        paragraph = Paragraph(f"• {item}", style)
        _, height = paragraph.wrap(w, 300)
        paragraph.drawOn(pdf, x, current_y - height)
        current_y -= height + gap
    return current_y


def draw_header(pdf: Canvas, styles: dict[str, ParagraphStyle], title: str, subtitle: str) -> None:
    """Draw the shared page header."""

    draw_paragraph(pdf, "AI FitFabrica", styles["tag"], MARGIN, PAGE_HEIGHT - 34, 180, 20)
    draw_paragraph(pdf, title, styles["h1"], MARGIN, PAGE_HEIGHT - 58, PAGE_WIDTH - (MARGIN * 2), 40)
    draw_paragraph(pdf, subtitle, styles["small"], MARGIN, PAGE_HEIGHT - 85, PAGE_WIDTH - (MARGIN * 2), 22)


def draw_chip(pdf: Canvas, x: float, y: float, text: str, fill: colors.Color, text_color: colors.Color = TEXT) -> None:
    """Draw a compact pill label."""

    width = max(58, len(text) * 5.2 + 20)
    pdf.setFillColor(fill)
    pdf.setStrokeColor(fill)
    pdf.roundRect(x, y, width, 18, 9, fill=1, stroke=0)
    pdf.setFillColor(text_color)
    pdf.setFont("BodyBold", 8)
    pdf.drawString(x + 10, y + 5.5, text)


def draw_arrow(pdf: Canvas, x1: float, y1: float, x2: float, y2: float, color: colors.Color = AI) -> None:
    """Draw a straight arrow between two points."""

    pdf.setStrokeColor(color)
    pdf.setLineWidth(1.4)
    pdf.line(x1, y1, x2, y2)
    pdf.line(x2, y2, x2 - 7, y2 + 4)
    pdf.line(x2, y2, x2 - 7, y2 - 4)


def draw_box_label(pdf: Canvas, x: float, y: float, w: float, h: float, label: str, fill: colors.Color) -> None:
    """Draw a labeled diagram box."""

    draw_panel(pdf, x, y, w, h, fill=fill)
    pdf.setFont("BodyBold", 9)
    pdf.setFillColor(TEXT)
    pdf.drawCentredString(x + (w / 2), y + (h / 2) - 3, label)


def draw_sitemap_page(pdf: Canvas, styles: dict[str, ParagraphStyle]) -> None:
    """Render the site-wide visual map."""

    draw_page_background(pdf)
    draw_header(pdf, styles, "Полная карта сайта", "Отдельные контуры: public website и workspace. Стрелки показывают основные переходы и CTA.")

    left_x = MARGIN
    top_y = PAGE_HEIGHT - 128
    public_w = 360
    workspace_w = 360

    draw_panel(pdf, left_x, 72, public_w, 420)
    draw_panel(pdf, PAGE_WIDTH - MARGIN - workspace_w, 72, workspace_w, 420)
    draw_paragraph(pdf, "Public website", styles["h2"], left_x + 18, top_y, 200, 20)
    draw_paragraph(pdf, "Workspace", styles["h2"], PAGE_WIDTH - MARGIN - workspace_w + 18, top_y, 200, 20)

    public_routes = [("/", "Главная"), ("/for-you", "Для себя"), ("/business", "Для бизнеса"), ("/capabilities", "Возможности"), ("/how-it-works", "Как работает"), ("/pricing", "Тарифы"), ("/privacy", "Безопасность"), ("/contacts", "Контакты"), ("/sign-in", "Вход")]
    workspace_routes = [("/workspace", "Кабинет"), ("/workspace/try-on/new", "Новая примерка"), ("/workspace/try-on/result", "Результат"), ("/workspace/outfit-builder", "Подбор образа"), ("/workspace/similar", "Найти похожее"), ("/workspace/product-card", "Карточка товара"), ("/workspace/content-package", "Контент-пакет"), ("/workspace/style-profile", "Профиль стиля"), ("/workspace/business-profile", "Профиль бизнеса"), ("/workspace/credits", "Кредиты"), ("/workspace/history", "История")]

    public_positions = {}
    y = 438
    for route, label in public_routes:
        draw_box_label(pdf, left_x + 20, y, public_w - 40, 28, f"{label}  {route}", colors.HexColor("#FFF7EF"))
        public_positions[route] = (left_x + public_w - 20, y + 14)
        y -= 38

    workspace_positions = {}
    y = 438
    for route, label in workspace_routes:
        draw_box_label(pdf, PAGE_WIDTH - MARGIN - workspace_w + 20, y, workspace_w - 40, 28, f"{label}  {route}", colors.HexColor("#F8F4FF"))
        workspace_positions[route] = (PAGE_WIDTH - MARGIN - workspace_w + 20, y + 14)
        y -= 34

    hub_x = PAGE_WIDTH / 2 - 90
    draw_panel(pdf, hub_x, 235, 180, 92, fill=colors.white)
    draw_paragraph(pdf, "Навигационный мост", styles["h2"], hub_x + 18, 305, 150, 20)
    draw_paragraph(pdf, "Header CTA и формы переводят пользователя из public contour в workspace или в demo-диалог.", styles["small"], hub_x + 18, 283, 144, 50)

    draw_arrow(pdf, public_positions["/"][0], public_positions["/"][1], hub_x, 280)
    draw_arrow(pdf, public_positions["/for-you"][0], public_positions["/for-you"][1], hub_x, 270)
    draw_arrow(pdf, public_positions["/business"][0], public_positions["/business"][1], hub_x, 260)
    draw_arrow(pdf, hub_x + 180, 280, workspace_positions["/workspace"][0], workspace_positions["/workspace"][1])
    draw_arrow(pdf, hub_x + 180, 260, workspace_positions["/workspace/try-on/new"][0], workspace_positions["/workspace/try-on/new"][1])

    pdf.showPage()


def draw_layout_diagram(pdf: Canvas, page: dict, x: float, y: float, w: float, h: float) -> None:
    """Draw a visual wireframe for the page type."""

    draw_panel(pdf, x, y, w, h)
    if page["layout"] == "public":
        draw_box_label(pdf, x + 16, y + h - 48, w - 32, 26, "Header", colors.HexColor("#FAF1E6"))
        draw_box_label(pdf, x + 16, y + 126, w * 0.54, 68, "Hero + copy", colors.white)
        draw_box_label(pdf, x + w * 0.60, y + 126, w * 0.22, 68, "Visual", colors.HexColor("#FBF6EF"))
        draw_box_label(pdf, x + 16, y + 92, w - 32, 24, "Final CTA / footer transition", colors.HexColor("#F6EFE7"))
        draw_box_label(pdf, x + 16, y + 48, w - 32, 30, "Feature grid", colors.HexColor("#FFF7EF"))
        draw_box_label(pdf, x + 16, y + 12, w - 32, 24, "Story / process block", colors.white)
    elif page["layout"] == "form":
        draw_box_label(pdf, x + 16, y + h - 48, w - 32, 26, "Header", colors.HexColor("#FAF1E6"))
        draw_box_label(pdf, x + 16, y + 18, w * 0.56, h - 82, "Form area", colors.white)
        draw_box_label(pdf, x + w * 0.62, y + 18, w * 0.22, h - 82, "Visual placeholder", colors.HexColor("#FBF6EF"))
    else:
        draw_box_label(pdf, x + 14, y + 18, w * 0.18, h - 36, "Sidebar", colors.HexColor("#F5F0E9"))
        draw_box_label(pdf, x + w * 0.22, y + h - 76, w * 0.40, 54, "Main hero", colors.white)
        draw_box_label(pdf, x + w * 0.64, y + h - 76, w * 0.18, 54, "Status cards", colors.HexColor("#FBF6EF"))
        draw_box_label(pdf, x + w * 0.22, y + 96, w * 0.34, h - 190, "Preview / main work area", colors.white)
        draw_box_label(pdf, x + w * 0.58, y + 96, w * 0.24, h - 190, "AI / status panel", colors.HexColor("#F8F4FF"))
        draw_box_label(pdf, x + w * 0.22, y + 18, w * 0.60, 58, "Bottom panels", colors.HexColor("#F6EFE7"))


def draw_route_page(pdf: Canvas, styles: dict[str, ParagraphStyle], page: dict) -> None:
    """Render one PDF sheet for a single route."""

    draw_page_background(pdf)
    draw_header(pdf, styles, f"{page['title']}  {page['route']}", f"{page['contour']} route. Описание страницы, блоков, переходов и файлов-источников.")

    draw_chip(pdf, MARGIN, PAGE_HEIGHT - 112, page["contour"], colors.HexColor("#EFEAFD"), AI)
    draw_chip(pdf, MARGIN + 92, PAGE_HEIGHT - 112, page["route"], colors.HexColor("#EEE6DA"), TEXT)

    left_w = 365
    right_x = MARGIN + left_w + 18
    right_w = PAGE_WIDTH - right_x - MARGIN
    top_y = PAGE_HEIGHT - 144
    bottom = 48

    draw_panel(pdf, MARGIN, bottom, left_w, top_y - bottom)
    draw_paragraph(pdf, "Роль страницы", styles["h2"], MARGIN + 18, top_y - 12, 180, 20)
    draw_paragraph(pdf, page["purpose"], styles["body"], MARGIN + 18, top_y - 42, left_w - 36, 86)
    draw_paragraph(pdf, "Что находится на странице", styles["h2"], MARGIN + 18, top_y - 128, 220, 20)
    next_y = draw_bullets(pdf, page["blocks"], MARGIN + 18, top_y - 154, left_w - 36, styles["body"])
    draw_paragraph(pdf, "Основные переходы", styles["h2"], MARGIN + 18, next_y - 8, 220, 20)
    next_y = draw_bullets(pdf, page["buttons"], MARGIN + 18, next_y - 34, left_w - 36, styles["body"])
    draw_paragraph(pdf, "Файлы-источники", styles["h2"], MARGIN + 18, next_y - 8, 220, 20)
    draw_bullets(pdf, page["sources"], MARGIN + 18, next_y - 34, left_w - 36, styles["small"], gap=3)

    draw_layout_diagram(pdf, page, right_x, 210, right_w, 242)
    draw_panel(pdf, right_x, bottom, right_w, 140)
    draw_paragraph(pdf, "Как страница включена в общую навигацию", styles["h2"], right_x + 18, 166, 280, 20)
    nav_text = (
        "Public pages связаны верхним header и footer. "
        if page["contour"] == "Public"
        else "Workspace pages связаны общим sidebar и маршрутами следующего действия. "
    )
    nav_text += "На схеме выше показана типовая композиция этой страницы и ее место внутри контура."
    draw_paragraph(pdf, nav_text, styles["body"], right_x + 18, 138, right_w - 36, 60)
    pdf.showPage()


def draw_file_map_page(pdf: Canvas, styles: dict[str, ParagraphStyle]) -> None:
    """Render the file responsibility page."""

    def start_sheet() -> tuple[float, list[float], float, int]:
        """Start a new file-map sheet and return its layout state."""

        draw_page_background(pdf)
        draw_header(pdf, styles, "Какие файлы за что отвечают", "Отдельный лист по текстам, layout, стилям, картинкам, формам, API и шрифтам.")
        column_width = (PAGE_WIDTH - (MARGIN * 2) - 18) / 2
        return column_width, [MARGIN, MARGIN + column_width + 18], PAGE_HEIGHT - 128, 0

    col_w, x_positions, y, col_index = start_sheet()

    for group in FILE_GROUPS:
        panel_h = 132
        if y - panel_h < 54 and col_index == 0:
            col_index += 1
            y = PAGE_HEIGHT - 128
        elif y - panel_h < 54 and col_index == 1:
            pdf.showPage()
            col_w, x_positions, y, col_index = start_sheet()
        x = x_positions[col_index]
        draw_panel(pdf, x, y - panel_h, col_w, panel_h)
        draw_paragraph(pdf, group["group"], styles["h2"], x + 16, y - 12, col_w - 32, 20)
        after_items = draw_bullets(pdf, group["items"], x + 16, y - 38, col_w - 32, styles["small"], gap=2)
        draw_paragraph(pdf, group["note"], styles["small"], x + 16, after_items - 4, col_w - 32, 44)
        y -= panel_h + 14

    pdf.showPage()


def build_pdf(output_path: Path) -> None:
    """Build the full PDF document."""

    register_fonts()
    styles = make_styles()
    pdf = Canvas(str(output_path), pagesize=landscape(A4))
    pdf.setTitle("AI FitFabrica - карта сайта и описание страниц")

    draw_sitemap_page(pdf, styles)
    for page in PAGES:
        draw_route_page(pdf, styles, page)
    draw_file_map_page(pdf, styles)
    pdf.save()


def main() -> None:
    """Generate the PDF into the requested folder."""

    output_dir = Path(r"C:\Madi\00 Мой Бизнес\Ai_FitFabrica\Доки")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "AI_FitFabrica_Карта_сайта_и_страницы.pdf"
    build_pdf(output_path)
    print(output_path)


if __name__ == "__main__":
    main()
