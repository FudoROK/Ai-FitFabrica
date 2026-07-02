# Integrated Roadmap After First Real Try-On Smoke

Дата: 2026-06-23

## 1. Почему нужен этот документ

После первого реального Try-On smoke система технически сработала:

- backend создал job;
- реальная генерация прошла;
- результат сохранился;
- результат открылся на сайте;
- quality baseline вернул `pass`.

Но тест показал продуктовую деталь: одежда может быть надета технически допустимо, но не оптимально по стилю. В нашем примере рубашка оказалась заправлена в джинсы, хотя визуально лучше было бы носить её навыпуск.

Это не отменяет старый план. Это добавляет новый слой в правильное место старого плана.

## 2. Старый план до этой находки

До обнаружения Wear Controls следующий порядок был:

1. Закрыть первый реальный Try-On smoke.
2. Garment Identity Agent live acceptance.
3. Material / Texture Agent live acceptance.
4. Try-On Instruction Agent live acceptance.
5. Quality Verifier Agent baseline.
6. Repair Agent / image edit pipeline.
7. Model routing config.
8. Marketplace / Similar / Cheaper Search.
9. Recalibration после реальных прогонов.

Этот порядок остаётся базовым.

## 3. Что изменилось

Появился новый продуктовый слой:

```text
Garment Wear Controls
```

Он отвечает за то, как вещь должна быть надета:

- рубашка: навыпуск, заправить, частично заправить, расстегнуть поверх;
- куртка: расстегнуть, застегнуть, накинуть;
- худи: капюшон надет, капюшон снят, oversize;
- джинсы: обычная посадка, высокая посадка, подвороты;
- платье: сохранить длину, с поясом, без пояса.

Важно: это не новый агент. Это backend-контур, который использует существующих агентов.

## 4. Как новый слой встраивается в старый план

Правильная цепочка становится такой:

```text
Human Identity
-> Garment Identity
-> Garment Wear Controls
-> Material / Texture
-> Try-On Instruction
-> Generation
-> Quality Verifier
-> Repair / Retry
-> Result
```

Почему именно так:

- сначала надо понять одежду;
- потом определить допустимые способы ношения;
- потом material/texture уточняет визуальные свойства;
- потом Try-On Instruction получает выбранный способ ношения;
- потом Quality Verifier проверяет, соблюдён ли он;
- потом Repair может исправить локальную ошибку.

## 5. Новый общий порядок работ

### Этап 1. Закрыть первый реальный Try-On smoke

Статус: сделано.

Результат:

- job `try_on_f399a6aa932b4816854713b1d24889f0`;
- status `completed`;
- image endpoint работает;
- backend после перезапуска VM живой;
- safe sandbox mode восстановлен.

### Этап 2. Garment Identity live acceptance

Это всё ещё следующий обязательный шаг.

Нужно проверить, что агент правильно понимает:

- тип одежды;
- цвет;
- крой;
- длину;
- воротник;
- рукава;
- пуговицы/молнии;
- карманы;
- принт/логотип;
- неоднозначность;
- плохие фото;
- несколько вещей в кадре;
- не одежду.

Без этого нельзя качественно строить Wear Controls.

### Этап 3. Garment Wear Controls + Taxonomy foundation

После Garment Identity acceptance добавляем:

- справочник категорий одежды;
- справочник типов одежды;
- справочник способов ношения;
- связь "тип одежды -> допустимые способы ношения";
- выбранный пользователем способ ношения;
- auto mode;
- сохранение неизвестных типов как кандидатов.

Правило:

```text
AI предлагает -> человек утверждает -> backend применяет
```

### Этап 4. Admin taxonomy candidate flow

Система не добавляет новые типы одежды в production автоматически.

Она должна:

- увидеть неизвестный тип;
- сохранить кандидата;
- собрать примеры;
- показать в будущей админке;
- ждать решения человека.

Админ может:

- approve;
- reject;
- merge;
- rename and approve;
- needs more examples.

### Этап 5. Material / Texture Agent acceptance

Проверяем honesty policy:

- не выдумывать точный состав ткани;
- различать визуальную оценку и подтвержденный состав;
- честно писать ограничения.

### Этап 6. Try-On Instruction Agent with Wear Controls

Try-On Instruction Agent должен получать:

- human analysis;
- garment analysis;
- selected wear control;
- material/texture analysis;
- preservation rules.

Он должен превращать это в строгую инструкцию для генерации.

Например:

```text
Shirt must be worn untucked.
The hem must remain visible over the jeans.
Do not tuck the shirt into the waistband.
Preserve face, body proportions and pose.
```

### Этап 7. Quality Verifier with Wear Controls

Quality Verifier должен проверять:

- лицо;
- тело;
- позу;
- одежду;
- цвет;
- детали;
- артефакты;
- выбранный способ ношения.

Если пользователь выбрал "навыпуск", а рубашка заправлена, результат не должен быть чистым pass.

### Этап 8. Repair / image edit

Repair должен уметь исправлять безопасные локальные детали:

- носить навыпуск;
- заправить;
- расстегнуть;
- застегнуть;
- убрать/добавить подвороты;
- сделать свободнее;
- сделать по фигуре.

Repair не должен менять человека, тело, лицо или саму вещь.

### Этап 9. Admin Console

Admin Console не должна быть первым шагом.

Она нужна после того, как backend уже умеет создавать taxonomy candidates.

Первый модуль:

```text
/admin/taxonomy
```

Потом:

- `/admin/agents`;
- `/admin/jobs`;
- `/admin/quality`;
- `/admin/costs`;
- `/admin/users`;
- `/admin/settings`.

### Этап 10. Model routing

После стабилизации агентов:

- дешёвые модели для простых текстовых задач;
- vision tier для анализа одежды/человека;
- strong vision для финального качества;
- image model для generation/editing.

### Этап 11. Marketplace / Similar / Cheaper Search

После стабилизации Try-On и Product Card:

- approved APIs;
- partner feeds;
- seller catalog import;
- no hidden scraping;
- connector cost accounting.

## 6. Что делать прямо сейчас

Не начинать с админки.

Не начинать с нового UI.

Правильный следующий шаг:

```text
Garment Identity Agent live acceptance
```

Почему:

- он был следующим в старом плане;
- он нужен для Product Card;
- он нужен для Try-On;
- он нужен для Wear Controls;
- он нужен для Similar/Cheaper Search;
- он дешевле ловит ошибки до generation.

## 7. VM

VM нужна только для live acceptance и реальных provider-прогонов.

Если сейчас делаем Garment Identity live acceptance, VM нужна.

Если делаем только локальные документы, схемы, tests, contracts, VM можно выключить.

## 8. Decision

Новый слой принят как часть общего плана, но он не должен ломать порядок работ.

Финальный порядок:

1. Garment Identity live acceptance.
2. Wear Controls + taxonomy backend foundation.
3. Taxonomy candidates with human approval.
4. Material / Texture acceptance.
5. Try-On Instruction with selected wear control.
6. Quality Verifier with wear-control checks.
7. Repair for safe wear-control corrections.
8. Admin taxonomy UI.
9. Model routing.
10. Marketplace/Search.

