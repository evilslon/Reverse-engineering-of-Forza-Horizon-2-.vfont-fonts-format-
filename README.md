# Forza Horizon 2 VFONT Format Specification

**Reverse-engineered technical documentation for the `.vfont` font
container used by Forza Horizon 2.**


**This analysis was conducted using ChatGPT; I am not a programmer and cannot assist you with any questions.**

**Анализ проведён при помощи ChatGPT, я не программист и не смогу помочь вам с какими-либо вопросами.**


This repository documents the binary structure observed in original
Forza Horizon 2 font files and the practical rules established while
inspecting and testing them.

> **Scope:** Forza Horizon 2 only. Do not assume that this specification
> applies to `.vfont` files from other Forza titles.

## What is documented

The specification describes the `.vfont` files found in
`Mount\\media\\ui\\Fonts.zip`.

The examined FH2 files contain: - font name and header/service area; -
glyph metrics table; - pair-kerning table; - glyph geometry records; -
vertex data stored as four little-endian IEEE-754 binary16 (half-float)
values; - 16-bit triangle indices.

The documents include observed field offsets, record layouts, validation
rules, sample-file measurements, safe-editing recommendations, and a
standalone Python parser/validator.

## Examined original files

  File                 Glyphs   Kerning records
  ------------------ -------- -----------------
  `Anthem_A.vfont`        248             1,094
  `Anthem_B.vfont`        248             1,101
  `Anthem_C.vfont`        248             1,118
  `Anthem_D.vfont`        248               718
  `verdana.vfont`         298               498

These counts describe the examined samples, not every possible FH2 build
or every `.vfont` file.

## Important compatibility notes

-   `.vfont` is a game-specific binary format, not TTF, OTF, or
    OpenType.
-   Preserve unknown header bytes and fields unchanged.
-   Do not add or remove glyph records unless the relevant game-loading
    behavior has been independently established.
-   Keep glyph metrics and geometry record counts consistent.
-   Validate all geometry indices against their vertex counts.
-   A structurally valid file is not automatically guaranteed to load in
    the game. Final compatibility must be tested in the target FH2 build
    and mod-loading environment.

## Confidence and limitations

The specification separates observations confirmed by binary inspection
from empirical findings and fields whose meanings remain unknown.
Structural validation on the listed samples does not prove that every
undocumented field has been fully decoded, nor does it establish every
detail of the game's runtime rendering behavior.

The presence of a pair-kerning table in the examined files is a
binary-structure finding. The exact runtime handling of every kerning
entry should be treated as a separate engine-behavior question unless
verified by a controlled in-game test.

## Disclaimer

This is an independent community reverse-engineering project. It is not
official documentation and is not affiliated with or endorsed by
Playground Games, Xbox Game Studios, or Microsoft. Forza Horizon 2 and
related names are trademarks of their respective owners.

------------------------------------------------------------------------

# Спецификация формата VFONT в Forza Horizon 2

**Техническая документация по результатам реверс-инжиниринга контейнера
шрифтов `.vfont`, используемого в Forza Horizon 2.**

В репозитории описана бинарная структура, обнаруженная в оригинальных
файлах шрифтов Forza Horizon 2, а также практические правила,
установленные при их анализе и проверке.

> **Область действия:** только Forza Horizon 2. Не следует считать, что
> эта спецификация подходит для `.vfont` из других игр серии Forza.

## Что описано

Спецификация посвящена отдельным файлам `.vfont`, находящимся в
`Mount\\media\\ui\\Fonts.zip`.

В исследованных файлах FH2 обнаружены: - имя шрифта и служебная область
заголовка; - таблица метрик глифов; - таблица парного кернинга; -
геометрические записи глифов; - данные вершин в формате четырёх
little-endian IEEE-754 binary16 (half-float) значений; - 16-битные
индексы треугольников.

В документации приведены наблюдаемые смещения полей, структура записей,
правила проверки, характеристики исследованных образцов, рекомендации по
безопасному редактированию, а также самостоятельный Python-парсер и
валидатор.

## Исследованные оригинальные файлы

  Файл                 Глифы   Записи кернинга
  ------------------ ------- -----------------
  `Anthem_A.vfont`       248             1 094
  `Anthem_B.vfont`       248             1 101
  `Anthem_C.vfont`       248             1 118
  `Anthem_D.vfont`       248               718
  `verdana.vfont`        298               498

Эти значения относятся к исследованным образцам и не являются
утверждением о каждом возможном билде FH2 или любом файле `.vfont`.

## Важные замечания о совместимости

-   `.vfont` --- специализированный бинарный формат игры, а не TTF, OTF
    или OpenType.
-   Неизвестные байты и поля заголовка следует сохранять без изменений.
-   Не добавляйте и не удаляйте записи глифов, пока поведение загрузчика
    игры не будет независимо проверено.
-   Сохраняйте согласованность количества записей метрик и геометрии.
-   Проверяйте, что все индексы геометрии находятся в пределах
    количества вершин.
-   Структурно корректный файл не обязательно гарантированно загрузится
    в игре. Итоговую совместимость необходимо проверять на целевой
    версии FH2 и в используемом окружении модификаций.

## Достоверность и ограничения

Спецификация отделяет наблюдения, подтверждённые бинарным анализом, от
эмпирических результатов и полей, назначение которых пока неизвестно.
Проверка структуры перечисленных образцов не доказывает, что все
неизвестные поля полностью расшифрованы, и не устанавливает все детали
работы игрового рендеринга во время выполнения.

Наличие таблицы парного кернинга в исследованных файлах --- вывод из
бинарной структуры. Точный способ применения каждой записи кернинга
игровым движком следует считать отдельным вопросом, пока он не
подтверждён контролируемым тестом непосредственно в игре.

## Отказ от ответственности

Это независимый проект по реверс-инжинирингу, созданный сообществом. Он
не является официальной документацией и не связан с Playground Games,
Xbox Game Studios или Microsoft и не одобрен ими. Forza Horizon 2 и
связанные с ней названия являются товарными знаками соответствующих
владельцев.
