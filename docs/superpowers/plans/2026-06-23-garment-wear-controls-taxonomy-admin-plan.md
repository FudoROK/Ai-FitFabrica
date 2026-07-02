# Garment Wear Controls, Learning Taxonomy and Admin Console Plan

Дата: 2026-06-23

## 1. Цель

Добавить в AI FitFabrica enterprise-контур, который управляет тем, как одежда должна быть надета в Try-On и связанных fashion-commerce workflow.

Контур называется `Garment Wear Controls`.

Он решает проблему вроде:

- рубашку лучше носить навыпуск, а не заправлять;
- пиджак должен быть расстегнут или застегнут;
- худи может быть oversize, hood up или hood down;
- брюки могут быть с подворотами или без;
- платье должно сохранить длину или использовать пояс.

Главный принцип: пользователь не пишет сложный prompt. Пользователь выбирает понятные варианты, а backend превращает выбор в строгий структурированный control для агентов, генерации, проверки качества и repair.

## 2. Место в общем плане проекта

Этот контур не является отдельным новым агентом.

Он встраивается в существующую цепочку:

```text
Human Identity
-> Garment Identity
-> Material / Texture
-> Garment Wear Controls
-> Try-On Instruction
-> Generation
-> Quality Verifier
-> Repair / Retry
-> Result
```

Почему именно здесь:

- `Garment Identity Agent` уже определяет тип, крой, длину, детали и ограничения одежды.
- `Wear Controls` используют эти факты и определяют допустимые способы ношения.
- `Try-On Instruction Agent` должен включить выбранный control в generation instruction.
- `Quality Verifier Agent` должен проверить, выполнен ли выбранный control.
- `Repair Agent` должен уметь исправлять локальное нарушение control, если это безопасно.

## 3. Что НЕ делаем

- Не создаем отдельного `Wear Control Agent` на первом этапе.
- Не даем frontend прямой prompt к AI.
- Не разрешаем агенту самому добавлять production-типы одежды без проверки.
- Не показываем пользователю весь огромный список настроек.
- Не включаем chaotic A2A между агентами.

## 4. Product UX

На странице Try-On после загрузки фото одежды появляется блок:

```text
Как носить вещь?

[Авто] [Навыпуск] [Заправить] [Частично заправить] [Расстегнуть поверх]
```

Но список зависит от конкретной вещи.

Пример для рубашки:

- `auto`
- `untucked`
- `tucked`
- `half_tucked`
- `open_layer`

Пример для куртки:

- `auto`
- `open`
- `closed`
- `draped`

Пример для джинсов:

- `auto`
- `regular_rise`
- `high_rise`
- `cuffed`

Если агент не уверен в типе одежды, backend показывает только безопасный `auto` и 1-2 общих варианта.

## 5. Backend taxonomy model

Нужен backend-owned catalog, а не hardcoded UI-список.

Базовые сущности:

```text
garment_taxonomy_items
- id
- parent_id
- category
- code
- display_name
- description
- active
- version
- created_at
- updated_at

garment_wear_controls
- id
- taxonomy_item_id
- control_code
- display_name
- description
- instruction_template
- risk_level
- active
- version

garment_taxonomy_candidates
- id
- proposed_code
- proposed_display_name
- proposed_parent_id
- proposed_category
- proposed_controls
- source_job_ids
- examples_count
- confidence
- agent_reasoning_summary
- status
- reviewer_decision
- reviewed_by
- reviewed_at
- created_at

garment_taxonomy_audit_log
- id
- actor_id
- action
- entity_type
- entity_id
- before_json
- after_json
- created_at
```

## 6. Initial taxonomy MVP

Не нужно сразу описывать все типы одежды в мире.

Стартуем с иерархии:

```text
tops
- shirt
- t_shirt
- blouse
- polo
- hoodie
- sweater
- cardigan
- vest

outerwear
- jacket
- coat
- blazer

bottoms
- jeans
- trousers
- shorts
- skirt

dresses
- dress
- jumpsuit

sets
- suit
- tracksuit
```

Этого достаточно, чтобы закрыть большинство первых B2C/B2B кейсов.

## 7. Garment Identity changes

`Garment Identity Agent` должен возвращать:

```json
{
  "garment_type": "shirt",
  "taxonomy_confidence": 0.86,
  "taxonomy_parent": "tops",
  "wear_control_candidates": [
    {
      "control_code": "untucked",
      "recommended": true,
      "confidence": 0.84,
      "reason": "Relaxed hip-length shirt is visually suitable for untucked wear."
    },
    {
      "control_code": "tucked",
      "recommended": false,
      "confidence": 0.63,
      "risk": "May look less natural because the fit is relaxed."
    }
  ],
  "unknown_taxonomy_candidate": null
}
```

Backend обязан:

- проверить, что `garment_type` существует в catalog;
- проверить, что `control_code` разрешен для этого типа или родительской категории;
- отбросить неизвестные control;
- если тип неизвестный, сохранить candidate, но не добавлять его в production catalog автоматически.

## 8. Auto mode

`auto` не означает “модель сама как-нибудь решит”.

`auto` означает:

```text
Backend chooses recommended wear control
based on Garment Identity + Fashion Stylist logic + catalog policy.
```

Если рекомендация неуверенная, backend выбирает safe default.

Например:

- relaxed shirt -> `untucked`;
- formal dress shirt with clear waistband styling -> `tucked`;
- jacket -> `open`;
- coat -> `open` or `closed` based on visible garment state;
- jeans -> `regular_rise`.

## 9. Try-On Instruction changes

`Try-On Instruction Agent` получает:

- human analysis;
- garment analysis;
- material analysis;
- selected wear control;
- instruction template from backend catalog;
- preservation requirements.

Он должен вернуть generation instruction, где wear control является обязательным ограничением.

Пример:

```text
The shirt must be worn untucked.
The hem must remain visible over the jeans.
Do not tuck the shirt into the waistband.
Preserve the person's face, body proportions and pose.
Preserve the garment color, collar, sleeve length and buttons.
```

## 10. Quality Verifier changes

Quality Verifier должен получить expected wear control и проверить:

```json
{
  "wear_control_match": {
    "expected": "untucked",
    "actual": "tucked",
    "status": "fail",
    "severity": "repairable",
    "confidence": 0.82
  }
}
```

Если выбранный control нарушен, результат не должен считаться полноценным `pass`.

Backend decision:

- `pass`: control выполнен;
- `repair`: локальная правка возможна;
- `retry`: control нарушен грубо или repair небезопасен;
- `reject/request_better_input`: входные данные не позволяют выполнить control.

## 11. Repair flow

После результата пользователь может нажать:

```text
Исправить деталь
```

Первые быстрые действия:

- носить навыпуск;
- заправить;
- частично заправить;
- расстегнуть;
- застегнуть;
- сделать свободнее;
- сделать по фигуре;
- убрать подвороты;
- добавить подвороты.

Frontend показывает только controls, доступные для конкретного результата.

Repair Agent получает не свободный текст, а backend-approved repair action.

## 12. Learning loop

Система может постепенно учиться новым типам одежды, но только через approval loop.

Схема:

```text
Unknown garment detected
-> backend saves taxonomy candidate
-> candidate accumulates examples
-> admin reviews candidate
-> approve / reject / merge / rename / needs more examples
-> approved item enters production catalog
-> audit log records decision
-> golden sample can be created
```

Production catalog нельзя менять полностью автоматически.

## 13. Admin Console

Нужен закрытый раздел:

```text
/admin
```

Первый модуль:

```text
/admin/taxonomy
```

Функции:

- смотреть новые предложенные типы одежды;
- видеть примеры фото/jobs;
- видеть confidence и reasoning summary;
- видеть похожие существующие типы;
- approve;
- reject;
- merge with existing;
- rename and approve;
- mark as needs more examples;
- управлять wear controls для утвержденного типа;
- смотреть audit log.

Позже модули admin console:

- `/admin/agents`;
- `/admin/jobs`;
- `/admin/quality`;
- `/admin/costs`;
- `/admin/users`;
- `/admin/settings`.

На первом этапе реализуется только taxonomy review foundation.

## 14. Security and governance

Admin actions требуют:

- admin auth;
- role check;
- audit log;
- no public access;
- no direct mutation from frontend without backend validation.

Если admin auth еще не готов, backend endpoints остаются disabled или доступны только в локальном/test контуре.

## 15. Implementation phases

### Phase 1 - Domain and catalog foundation

- Add domain models for taxonomy item, wear control, candidate and audit event.
- Add SQL migration.
- Add repository ports.
- Add initial seed catalog.
- Add unit tests for allowed controls, fallback and unknown candidate creation.

### Phase 2 - Garment Identity contract extension

- Extend Garment Identity contract with taxonomy classification and wear control candidates.
- Update prompt_config.
- Add backend mapper and policy validation.
- Add tests for invalid unknown controls and low-confidence taxonomy.

### Phase 3 - Try-On options and UI

- Add `selected_wear_control` to Try-On job options.
- Add frontend block "Как носить вещь?".
- Add loading/empty/error/disabled states.
- Add typed API usage.
- Do not allow arbitrary prompt text.

### Phase 4 - Try-On Instruction integration

- Pass selected control into Try-On Instruction Agent.
- Add instruction policy checks requiring wear control when selected.
- Add tests that instruction includes required control and excludes opposite control.

### Phase 5 - Quality Verifier integration

- Extend quality report with wear control check.
- Backend policy must override unsafe pass if selected control is violated.
- Add golden tests for tucked vs untucked, open vs closed, cuffed vs uncuffed.

### Phase 6 - Repair actions

- Add backend-approved repair actions for wear control defects.
- Add UI "Исправить деталь".
- Add repair policy: local-only, no identity/body/garment replacement.
- Add second Quality Verifier after repair.

### Phase 7 - Admin taxonomy review

- Add admin-only taxonomy candidate endpoints.
- Add `/admin/taxonomy` UI.
- Add approve/reject/merge/rename flows.
- Add audit log.
- Keep disabled until admin auth is production-ready.

### Phase 8 - Live acceptance and recalibration

- Run dataset across shirts, jackets, hoodies, jeans, dresses and ambiguous garments.
- Measure false controls, false recommendations and repair success rate.
- Update catalog and model routing based on real results.

## 16. Acceptance criteria

- User sees only relevant wear controls for the uploaded garment.
- `auto` produces a backend-owned explicit selected control.
- Try-On generation instruction includes selected control.
- Quality Verifier checks selected control.
- Wrong control cannot be accepted as clean pass.
- Repair can fix safe local control defects.
- Unknown garment types become candidates, not production rules.
- Admin can approve/reject/merge candidates with audit log.
- No direct AI calls from frontend.
- No unapproved production taxonomy mutation.

## 17. Recommended priority in current project roadmap

Current project priority stays:

1. Finish Garment Identity live acceptance.
2. Add taxonomy and wear controls foundation while extending Garment Identity.
3. Run Material / Texture honesty acceptance.
4. Integrate wear controls into Try-On Instruction.
5. Add Quality Verifier wear-control checks.
6. Add Repair wear-control actions.
7. Build `/admin/taxonomy` after backend candidate flow exists.

Reason:

Garment Identity is the source of truth for clothing understanding. Wear Controls should not be built before Garment Identity acceptance, but the taxonomy contract should be designed now because it changes what Garment Identity must return.

