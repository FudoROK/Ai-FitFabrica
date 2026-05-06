# AI FitFabrica DESIGN.md — Final Design System for Stitch

## 0. Purpose

This file is the strict visual design system for AI FitFabrica.

Use it to design the website and product interface in Google Stitch.

This file defines:
- visual style
- colors
- typography
- spacing
- layout principles
- components
- responsive behavior
- UI states
- content tone

This file does not define:
- page list
- page-by-page content
- backend logic
- database logic
- API logic
- payment logic
- technical implementation

If another prompt describes pages, that prompt must follow this DESIGN.md.
If there is a conflict, this DESIGN.md controls the visual style.

---

## 1. Core Design Principle

AI FitFabrica uses a product-first visual system.

The interface must feel:
- calm
- minimal
- precise
- premium
- trustworthy
- fashion-aware
- technically controlled

The interface must not dominate.
The content, product visuals, uploaded items, generated results and next actions must dominate.

The design must feel like an Apple-style product presentation adapted for a fashion-AI platform.

The product must not feel like:
- a chatbot
- a marketplace catalog
- a generic AI image generator
- a crypto / neon / cyberpunk AI tool
- a heavy SaaS dashboard
- a template startup landing page

---

## 2. Visual Philosophy

Style direction:

**Apple.com-inspired product presentation + premium fashion-tech warmth.**

The public website must feel:
- spacious
- cinematic
- product-led
- visual-first
- minimal
- confident

The workspace must feel:
- clean
- calm
- operational
- premium
- easy to understand
- not like an admin panel

The visual language should combine:
- Apple-like clarity
- fashion editorial spacing
- warm ivory surfaces
- soft rounded geometry
- restrained AI indicators
- clear product result previews

Core rule:

**One section = one strong idea.**

No screen should feel crowded.
No section should try to explain everything at once.

---

## 3. Design Tokens

```yaml
name: AI FitFabrica
version: final
style: Apple-inspired premium fashion-tech
language: Russian UI copy

colors:
  background: "#F7F3EC"
  surface: "#FFFDF8"
  surface_alt: "#F1EAE0"
  surface_soft: "#F2E8D9"

  primary: "#141414"
  on_primary: "#FFFFFF"

  text_primary: "#141414"
  text_secondary: "#5F5F63"
  text_muted: "#8B8580"

  border: "#E8E1D6"
  divider: "#DED6CB"

  ai: "#6E56CF"
  ai_hover: "#5B45B8"
  ai_soft: "#EFEAFD"

  fashion_accent: "#D8C3A5"
  fashion_accent_soft: "#F2E8D9"

  success: "#2F8F6B"
  success_soft: "#E8F5EF"

  warning: "#D96C5F"
  warning_soft: "#FBEDEA"

  error: "#D93025"
  error_soft: "#FCE8E6"

  info: "#4F7FDB"
  info_soft: "#EAF1FF"

typography:
  display:
    fontFamily: "Manrope, Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "72px"
    fontWeight: 700
    lineHeight: 1.02
    letterSpacing: "-0.04em"

  h1:
    fontFamily: "Manrope, Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "56px"
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: "-0.035em"

  h2:
    fontFamily: "Manrope, Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "44px"
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "-0.03em"

  h3:
    fontFamily: "Manrope, Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "32px"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.02em"

  h4:
    fontFamily: "Manrope, Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "24px"
    fontWeight: 700
    lineHeight: 1.22
    letterSpacing: "-0.015em"

  body_large:
    fontFamily: "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "20px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "-0.01em"

  body:
    fontFamily: "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "-0.005em"

  small:
    fontFamily: "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.45

  caption:
    fontFamily: "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.35

  button:
    fontFamily: "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.005em"

  label:
    fontFamily: "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "14px"
    fontWeight: 600
    lineHeight: 1.2

  overline:
    fontFamily: "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "12px"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "0.08em"

spacing:
  base: "8px"
  micro: "4px"
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  xxl: "48px"
  section_sm: "64px"
  section_md: "96px"
  section_lg: "128px"
  section_xl: "144px"
  page_x_desktop: "72px"
  page_x_tablet: "40px"
  page_x_mobile: "20px"
  grid_gutter: "24px"
  content_max: "1280px"

radius:
  none: "0px"
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "24px"
  xl: "28px"
  xxl: "40px"
  full: "999px"

shadow:
  card: "0 16px 50px rgba(20, 20, 20, 0.06)"
  floating: "0 24px 70px rgba(20, 20, 20, 0.10)"
  modal: "0 32px 90px rgba(20, 20, 20, 0.16)"
```

---

## 4. Color Rules

Use Warm Ivory `#F7F3EC` as the main page background.
Use Silk White `#FFFDF8` for cards, panels, upload zones, previews and workspace surfaces.
Use Graphite `#141414` for main text and primary buttons.
Use Neutral Gray `#5F5F63` for secondary text, descriptions and inactive navigation.
Use Muted `#8B8580` for captions, helper text and disabled UI.

Use AI Violet `#6E56CF` only for AI-specific meaning:
- AI actions
- AI analysis
- active agent state
- quality verification
- generated recommendation
- repair suggestion
- processing status

Do not use violet as general decoration.

Use Champagne `#D8C3A5` only for subtle fashion/premium emphasis:
- premium labels
- soft dividers
- elegant highlights
- business/premium moments

Functional colors must be semantic:
- green only for verified success
- red only for real errors or destructive actions
- warning only for photo quality risks or repair suggestions
- blue only for neutral information

Forbidden:
- neon colors
- random bright accents
- multicolor gradients
- dark full-page backgrounds
- heavy colorful UI
- using violet everywhere because the product is AI

---

## 5. Typography Rules

Use Manrope for:
- hero titles
- section headlines
- large product statements
- editorial titles

Use Inter for:
- body copy
- navigation
- buttons
- forms
- captions
- workspace UI
- panels
- badges

Headlines must be short and powerful.
Maximum: 1–2 lines.

Body text must be clear and short.
Avoid long paragraphs.

UI copy must be in Russian.
Use clear Russian action labels.
Avoid hype, vague and weak wording.

Good button labels:
- Начать примерку
- Подобрать образ
- Найти похожее дешевле
- Создать карточку товара
- Запросить демо
- Сохранить результат
- Экспортировать пакет

Avoid weak labels:
- Подробнее
- Попробовать
- Узнать больше
- Далее
- Кликнуть

Use sentence case.
Avoid decorative typography.
Avoid ultra-light fonts.
Avoid all-caps except small badges or overline labels.

---

## 6. Layout Principles

### 6.1 One Block = One Idea

Each section or major block must communicate one concept only.

Do not mix multiple user goals inside one visual block.
If a section explains more than one concept, split it.

### 6.2 Product-First Layout

Each public section should be built around:
1. headline
2. strong visual
3. short supporting text
4. one clear action

The product/result visual is more important than decoration.

### 6.3 Apple-Like Product Rhythm

Public pages should use:
- large hero sections
- full-width visual storytelling
- generous whitespace
- minimal text
- strong product/result previews
- calm navigation
- one main focus per viewport

Avoid dense SaaS sections and feature grids.

### 6.4 Progressive Disclosure

Do not show all information at once.
Reveal information in this order:

**idea → result → detail → action**

### 6.5 Workspace Layout

Workspace screens should use:
- clear task title
- input area
- large preview/result area
- status or AI panel
- next action

Recommended desktop workspace pattern:
- left: inputs and controls
- center: main preview/result
- right: AI/status panel

Mobile workspace pattern:
- title
- preview/result
- inputs
- AI/status panel
- sticky main action

### 6.6 Visual Hierarchy

Each screen must have one dominant visual focus.
No competing hero blocks.
No multiple primary CTAs in one viewport.

---

## 7. Grid and Spacing

Use an 8px spacing system.
Use 4px only for micro-adjustments.

Desktop:
- 12-column grid
- max content width: 1280px
- horizontal page padding: 72px
- gutter: 24px
- section spacing: 96–144px

Tablet:
- horizontal padding: 40px
- two-column layouts may remain only if readable
- dense layouts collapse to fewer columns

Mobile:
- horizontal padding: 20px
- single-column stacking
- large previews stack above panels
- sticky bottom primary CTA on workflow screens

Public sections should feel open and cinematic.
Workspace sections should feel structured but not cramped.

---

## 8. Shapes and Radius

Use soft rounded geometry consistently.

Buttons:
- radius: 999px

Badges and chips:
- radius: 999px

Inputs:
- radius: 16px

Cards:
- radius: 24–28px

Large hero containers / preview panels:
- radius: 40px

Modals:
- radius: 28px

Do not mix sharp and rounded geometry.
Do not use random radii.
Do not use square buttons.

---

## 9. Elevation and Depth

Use minimal depth.
Primary separation should come from:
- whitespace
- tonal surfaces
- subtle warm borders

Borders:
- `1px solid #E8E1D6`

Default card shadow:
- `0 16px 50px rgba(20, 20, 20, 0.06)`

Floating panel shadow:
- `0 24px 70px rgba(20, 20, 20, 0.10)`

Modal shadow:
- `0 32px 90px rgba(20, 20, 20, 0.16)`

Forbidden:
- heavy black shadows
- stacked shadows
- noisy glassmorphism
- glossy plastic UI
- aggressive glow effects

AI glow may be used only subtly around active AI states, with very low opacity.

---

## 10. Components

### 10.1 Buttons

Primary button:
- Graphite background `#141414`
- white text
- pill shape
- used once per main section or screen
- used for the main action only

Secondary button:
- surface background or transparent
- graphite text
- subtle border
- pill shape
- used for second-level action

AI button:
- violet background `#6E56CF`
- white text
- used only for AI actions:
  - analyze
  - generate
  - verify
  - repair
  - recommend

Ghost button:
- transparent
- minimal
- used for navigation and utility actions

Disabled button:
- soft warm background
- muted text
- clearly inactive

### 10.2 Cards

Cards must be spacious and purposeful.

Use cards for:
- audience choices
- feature summaries
- saved results
- pricing plans
- product comparisons
- workspace panels

Do not overuse cards on public pages.
Do not create dense card grids as the main visual language.

Card rules:
- surface background
- subtle border
- radius 24–28px
- internal padding 24–32px
- short title
- short supporting text
- one action

### 10.3 Large Visual Panels

Use large visual panels for:
- hero visuals
- try-on previews
- product result previews
- before/after comparisons
- content package previews

Rules:
- radius 28–40px
- minimal border
- strong visual focus
- no cluttered overlays

### 10.4 Inputs

Inputs must have visible labels.
Do not rely on placeholder-only labels.

Input rules:
- height: 52px
- radius: 16px
- surface background
- warm border
- helper text allowed
- clear error state
- clear disabled state

### 10.5 Upload Zones

Upload zones must feel safe and trustworthy.

Rules:
- radius: 28px
- surface background
- dashed champagne border
- clear title
- short helper text
- accepted format note
- visible empty state
- hover state with soft fashion accent

### 10.6 AI Panels

AI panels must look like product system UI.
They must not look like chat bubbles.

Use AI panels for:
- analysis status
- quality checks
- fit/style suggestions
- pricing/trend recommendations
- repair suggestions
- credits estimate

AI panel structure:
- title
- short explanation
- checklist/status rows
- semantic badges
- one next action if needed

AI panels may use:
- `#EFEAFD` background
- violet badges
- subtle violet indicators

### 10.7 Badges and Chips

Badges:
- small
- pill-shaped
- semantic color
- short text

Badge types:
- success: verified / ready
- warning: risk / needs repair
- error: failed / blocked
- AI: analyzing / generated / recommended
- info: neutral information

### 10.8 Navigation

Public navigation:
- minimal
- calm
- lightweight
- Apple-like
- no heavy shadows
- no bulky header

Workspace navigation:
- clear but quiet
- sidebar on desktop
- compact drawer or bottom nav on mobile
- active item must be visible but not loud

---

## 11. UI States

Design reusable visual states.

### Empty State

Use when there is no upload, no result or no saved item.
Must include:
- clear short title
- one sentence explanation
- one primary action

### Uploading State

Must feel safe and controlled.
Show:
- progress indicator
- file preview if possible
- calm helper text

### Ready State

Show that the user can continue.
Use success or neutral indicators.

### Processing State

Use calm AI progress.
Avoid fake excessive animation.
Use subtle violet only for AI process.

### Quality Check State

Show checklist:
- person/photo quality
- garment/details
- color consistency
- result readiness

### Repair Needed State

Use warning color.
Explain calmly what needs correction.
Show one clear action.

### Result Ready State

Use success state.
Focus on result preview and next action.

### Error State

Use red only for real blocking issues.
Write human, clear error text.
Offer retry or alternative.

### No Credits State

Use neutral/warning tone.
Do not make it aggressive.
Show balance and top-up action.

---

## 12. Imagery and Visual Content

Use realistic fashion/product visuals.

Preferred visuals:
- clean human photo mockups
- garment/product photos
- before/after try-on compositions
- product card previews
- marketplace-style card previews without becoming a marketplace
- Instagram/content package previews
- comparison layouts

Avoid:
- abstract AI spheres
- random glowing blobs
- robotic faces
- cartoon avatars
- overly glamorous fashion clichés
- fake sci-fi dashboards
- cluttered stock photo collages

For B2C, visuals should feel personal and helpful.
For B2B, visuals should feel useful, commercial and ready for sales.

---

## 13. Content Tone

All UI copy must be in Russian.

Tone:
- calm
- direct
- premium
- useful
- human
- confident without hype

Avoid:
- marketing noise
- exaggerated promises
- vague AI buzzwords
- childish playful tone
- aggressive sales copy
- body-shaming language
- technical backend language

Good tone examples:
- “Примерьте вещь до покупки”
- “Проверьте, подходит ли фасон и цвет”
- “Создайте карточку товара из фото”
- “AI проверит результат перед выдачей”
- “Сохраните образ или найдите похожее дешевле”

Do not use:
- “революционный”
- “магический”
- “вау-эффект”
- “просто нажмите кнопку и получите всё”

---

## 14. Accessibility and Usability

Maintain strong readability and contrast.

Rules:
- visible labels for all inputs
- clear focus states
- readable text on all surfaces
- buttons must have clear actions
- touch targets must be comfortable on mobile
- do not hide key information in hover-only states
- do not use color as the only indicator
- avoid very small text for important information

---

## 15. Responsive Behavior

Desktop:
- public pages use wide Apple-like sections
- workspace uses structured columns
- navigation is horizontal on public pages
- workspace may use sidebar

Tablet:
- reduce columns
- preserve large visual hierarchy
- avoid cramped panels

Mobile:
- single-column layout
- compact navigation
- large readable headings
- previews stack before detailed panels
- main actions remain easy to reach
- workflow screens may use sticky bottom CTA

---

## 16. Prohibited Patterns

Do not use:
- chatbot UI as the main interface
- generic AI image generator UI
- marketplace catalog as the main layout
- dark cyberpunk style
- neon gradients
- random abstract AI blobs
- heavy SaaS dashboards
- dense feature grids
- 4x4 card walls
- excessive glassmorphism
- loud animation
- multiple competing primary CTAs
- cluttered screens
- tiny UI text
- unclear “Next” buttons
- technical backend diagrams

---

## 17. Final Design Check

Every generated screen must pass this checklist:

- Does it feel premium and calm?
- Is there one clear main idea?
- Is the main visual/result dominant?
- Is the next action obvious?
- Is the UI copy in Russian?
- Is violet used only for AI meaning?
- Is the screen spacious enough?
- Does it avoid marketplace/chatbot/SaaS-dashboard patterns?
- Does it follow DESIGN.md colors, typography and spacing?

If a screen feels complex, noisy or generic, redesign it.

