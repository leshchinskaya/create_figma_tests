../../../rigla-demo-specification/00 — ОБЩЕЕ/
├── section__ads-banners.md
├── section__catalog.md
├── section__my-purchases.md
├── section__symptoms.md
└── Термины и сокращения.md

../../../rigla-demo-specification/02 — КАТАЛОГ/
└── Mobile — Поиск.md



<file path="../../../rigla-demo-specification/00 — ОБЩЕЕ/section__ads-banners.md">
---
order: 2
title: section__ads-banners
---

## Входные параметры

| Название | Тип данных | Обязательность | Описание                               |
|----------|------------|----------------|----------------------------------------|
| model    | object     | \+             | С какого объекта в ответе брать данные |

## Поведение

Горизонтальный слайдер с баннерами. Поддерживает автопрокрутку и обработку переходов по ссылкам. Количество баннеров определяется количеством элементов массива banners.

Последний баннер циклически переходит к первому.

## Компоновка

**\- Figma Link:** <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=5-3285&t=AflWBiBGDB4WD9Jh-0>

\- **Swagger Model:** model

**\- Mapping:**

1. Баннер = imageUrl

**\- User Action:**

1. Тап на \_banner -> обработать ссылку `targetUrl`
</file>


<file path="../../../rigla-demo-specification/00 — ОБЩЕЕ/section__catalog.md">
---
order: 1.5
title: section__catalog
---

## Входные параметры

| Название | Тип данных | Обязательность | Описание                               |
|----------|------------|----------------|----------------------------------------|
| state    | string     | \+             | Тип товарного листинга                 |
| name     | string     | \+             | Название товарного листинга            |
| model    | object     | \+             | С какого объекта в ответе брать данные |

## Поведение

{% table header="row" %}

---

*  state = scroll-catalog

*  state = catalog

*  state = small-catalog

---

*  Карточки товаров выполнены как не зацикленный горизонтальный слайдер

   Можно пролистывать свайповм вправо/влево

*  Карточки товаров по два в строку расположены вертикально друг под другом

*  Карточки товаров по одной в строку расположены вертикально друг под другом

{% /table %}

## Компоновка

**\- Figma Link:**

| state = scroll-catalog                                                                              | state = catalog                                                                                     | state = small-catalog                                                                               |
|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=1-18974&t=6FjzpWxr2D0ob3hF-0> | <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=1-18974&t=6FjzpWxr2D0ob3hF-0> | <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=1-18974&t=6FjzpWxr2D0ob3hF-0> |

\- **Swagger Model:** model

**\- Mapping:**

1. headline = `name`

2. product_card (для state = scroll-catalog и state = catalog)

   1. image = `imageUrl`

   2. info.text = `name`

   3. rate = `rating`

   4. Отзывы =  `reviewsCount`

   5. price

      1. Если `oldPrice` > 0 -> отображаем две цены

         1. Перечеркнутая = `oldPrice`

         2. Неперечеркнутая = `price`

      2. Если `oldPrice` = 0 -> отображаем одну цену

         1. Неперечеркнутая = `price`

   6. Кнопка «Избранное» (favourites)

   7. Кнопка «Добавить в корзину» (add-button)

3. product_card (для state = small-catalog)

   1. image = `imageUrl`

   2. info.text = `name`

   3. price = `price`

   4. Кнопка «Добавить в корзину» (add-button)

**\- User Action:**

1. Тап на кнопку favourites

   1. Если не активна -> отправить запрос PUT /products/\{productId}/favorite

      1. Загрузка -> ничего

      2. Успех -> активировать кнопку

      3. Ошибка -> ничего

   2. Если активна -> отправить запрос DELETE /products/\{productId}/favorite

      1. Загрузка -> ничего

      2. Успех -> деактивировать кнопку

      3. Ошибка -> ничего

2. Тап на кнопку add-button

   1. Отправить запрос POST /cart/items

      1. Загрузка -> ничего

      2. Успех -> ничего

      3. Ошибка -> ничего

3. Тап на product-card -> открыть [деталку товара](./../product/mobile-product)
</file>


<file path="../../../rigla-demo-specification/00 — ОБЩЕЕ/section__my-purchases.md">
---
order: 1.8
title: section__my-purchases
---

## Входные параметры

| Название | Тип данных | Обязательность | Описание                               |
|----------|------------|----------------|----------------------------------------|
| scroll   | string     | \+             | Тип товарного листинга                 |
| name     | string     | \+             | Название товарного листинга            |
| model    | object     | \+             | С какого объекта в ответе брать данные |

## Компоновка

**Состояния**

| scroll = on                                                                                          | scroll = off                                                                                         |
|------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=193-5851&t=AflWBiBGDB4WD9Jh-0> | <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=193-5851&t=AflWBiBGDB4WD9Jh-0> |

\- **Swagger Model:** model

**\- Mapping:**

1. headline = `name`

2. product_card

   1. image = `imageUrl`

   2. Кнопка «Добавить в корзину» (add-button)

**\- User Action:**

1. Тап на кнопку add-button

   1. Отправить запрос POST /cart/items

      1. Загрузка -> ничего

      2. Успех -> ничего

      3. Ошибка -> ничего

2. Тап на product-card -> открыть [деталку товара](./../product/mobile-product)
</file>


<file path="../../../rigla-demo-specification/00 — ОБЩЕЕ/section__symptoms.md">
#### Секция "Частые симптомы

## Входные параметры

| Название       | Тип данных | Обязательность | Описание                             |
| -------------- | ---------- | -------------- | ------------------------------------ |
| Frame 61, text | string     | \+             | Наименование симптома вместе с emoji |

## Компоновка

**Состояния**

| **Figma Link**      | <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=193-19608&t=DqqO5Kb23toIJC3i-4> |
| ------------------- | ----------------------------------------------------------------------------------------------------- |
| **Figma Component** | `section__symptoms`                                                                                   |
| **Swagger Model     | GET /recommendations/symptoms`<br>`SymptomTag`                                                        |

**Mapping:**

1. Frame 61, text --> `SymptomTag.emoji + " " + SymptomTag.label`
	1. если emoji = nil/null -> не отображать симптом
	2. если label = nil/null -> не отображать симптом

**Действия:**

1. Выбрать симптом --> Открытие состояния Search Done [Поиска](obsidian://open?vault=rigla-demo-specification&file=02%20%E2%80%94%20%D0%9A%D0%90%D0%A2%D0%90%D0%9B%D0%9E%D0%93%2FMobile%20%E2%80%94%20%D0%9F%D0%BE%D0%B8%D1%81%D0%BA), вызов `GET /products?searchQuery={SymptomTag.label}`

3. Ошибка на запрос или данные не пришли --> Блок не отображается
</file>


<file path="../../../rigla-demo-specification/00 — ОБЩЕЕ/Термины и сокращения.md">
**АЗ** — авторизованная зона.

**НАЗ** — не авторизованная зона.
</file>


<file path="../../../rigla-demo-specification/02 — КАТАЛОГ/Mobile — Поиск.md">
## Исходные данные

-  **Swagger:** <https://surfstudio.gitlab.yandexcloud.net/internal/ai-boost/swagger-rigla/-/blob/main/rigla_swagger.yaml>

-  **Figma:**

   -  *First Session:* <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=191-4262&t=DqqO5Kb23toIJC3i-4>

   -  *Search:* <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=171-5895&t=DqqO5Kb23toIJC3i-4>

   -  *Categories:* <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=191-4657&t=DqqO5Kb23toIJC3i-4>

   -  *Done:* <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=191-18871&t=DqqO5Kb23toIJC3i-4>

## Use Cases

Экран [**Поиска**](https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=171-5895&t=DqqO5Kb23toIJC3i-4) обеспечивает универсальную точку входа для быстрого поиска лекарств/товаров аптеки.

### Начать поиск товара или симптома

-  Пользователь может открыть флоу поиска и ввести запрос вручную или выбрать из предлагаемых быстрых вариантов (например, из частых симптомов или истории).

#### Посмотреть историю запросов и быстрые варианты

-  Пользователь может ознакомиться с предыдущими поисковыми запросами (если такие были).

-  Пользователь может очистить историю поисков.

-  Пользователь может использовать часто встречающиеся симптомы или популярные поисковые варианты для мгновенного поиска.

### Получить релевантные подсказки по мере ввода

-  Пользователь может видеть автоматические подсказки по товарам и категориям в зависимости от введённого текста.

-  Пользователь может быстро выбирать подходящие предложения из подсказок.

### Посмотреть результаты поиска

-  Пользователь может ознакомиться со списком найденных товаров, соответствующих запросу.

-  Пользователь может просмотреть краткую информацию о каждом товаре (название, изображение, цена и т.д.).

-  Пользователь может узнать, сколько всего найдено результатов.

-  Пользователь может при необходимости -- перейти к полному списку результатов.

### Взаимодействовать с найденными товарами

-  Пользователь может открыть карточку товара для подробной информации.

-  Пользователь может добавить товар в корзину и избранное прямо из результатов поиска.

## Точки входа

1.  Таббар "Каталог" --> Открытие без `searchQuery`

2. Экран "Главная"  --> Открытие без `searchQuery`

3. Экран "Главная" -->  Открытие с `searchQuery`

## Логика инициализации

Вызываются параллельно следующие запросы:

1. `GET /recommendations/symptoms`,
   
   Обработка запроса
   
   🔄 **Загрузка** --> показываем  состояние загрузки. (см. Состояние "Загрузка")
   
   ⚠️ **Ошибка** --> показываем полноэкранный error state (см. Состояние "Ошибка").
   
   ❇️ **Успех** --> обновляем состояние экрана (см. Состояние "Данные").

3. `GET /search/history`, `GET /user/purchases`,
   
   Обработка запроса
   
   🔄 **Загрузка** --> показываем  состояние загрузки. (см. Состояние "Загрузка")
   
   ⚠️ **Ошибка** --> показываем полноэкранный error state (см. Состояние "Ошибка").
   
   ❇️ **Успех** --> обновляем состояние экрана (см. Состояние "Данные").

4. `GET /products` c `searchQuery`=text
   
   Обработка запроса
   
   🔄 **Загрузка** --> показываем  состояние загрузки. (см. Состояние "Загрузка")
   
   ⚠️ **Ошибка** --> показываем полноэкранный error state (см. Состояние "Ошибка").
   
   ❇️ **Успех** --> обновляем состояние экрана (см. Состояние "Данные").

## Лейаут

Могут быть такие состояния:

### 🔄 Состояние «Загрузка»

Skeleton‑лоадер: <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=398-14400&t=c8RmQvE2MsOKynEB-4>

### ⚠️ Состояние «Ошибка»

Полноэкранная stub‑страница + кнопка «Повторить», повторяющая все GET-запросы (`/recommendations/symptoms`, `/search/history`, `/user/purchases`, `/products/suggestions`, `/products`).

<https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=434-12423&t=R2Mg8sy8VtfCeBbE-4>

### ❇️ Состояние «Данные»

Лейаут состояния Данные может выглядеть следующим образом:

#### First Session

| **Figma Link**      | <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=191-4262&t=DqqO5Kb23toIJC3i-4> |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| **Figma Component** | `screen: First Session`                                                                              |
##### Состоит из секций
   - Секция "Поисковая строка
   - Секция "Частые симптомы"

##### Правила отображения
Отображается, когда
- НАЗ, пользователь ничего не вводил в поиск, точка входа без `searchQuery`
- АЗ, нет данных по секциям "Последние покупки", "История", пользователь ничего не вводил в поиск, точка входа без `searchQuery`

#### Search

| **Figma Link**      | <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=171-5895&t=DqqO5Kb23toIJC3i-4> |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| **Figma Component** | `screen: Search`                                                                                     |

##### Состоит из секций
   - Секция "Поисковая строка"
   - Секция "История"
   - Секция "Категории"
   - Секция "Последние покупки"

##### Правила отображения
Отображается, когда
- АЗ, есть данные по секциям "Последние покупки", "История", пользователь ничего не вводил в поиск, точка входа без `searchQuery`

#### Search categories

| **Figma Link**      | <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=191-4657&t=DqqO5Kb23toIJC3i-4> |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| **Figma Component** | `screen: Search categories`                                                                          |

##### Состоит из секций
   - Секция "Поисковая строка
   - Секция "Подсказки"
   - Секция "Действующее вещество"
   - Секция "Товары"

##### Правила отображения
Отображается, когда
- Пользователь вводит текст в поиск

#### Search Done

| **Figma Link**      | https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=191-18871&t=DqqO5Kb23toIJC3i-4 |
| ------------------- | --------------------------------------------------------------------------------------------------- |
| **Figma Component** | `screen: Search done`                                                                               |

##### Состоит из секций
   - Секция "Поисковая строка
   - Секция "Результаты поиска"

##### Правила отображения
Отображается, когда
- Пользователь подтвердил поиск на клавиатуре
- Точка входа с `searchQuery`

\___\_
#### Список секций
##### Секция "Поисковая строка"

|                     |                                                                                                       |
| ------------------- | ----------------------------------------------------------------------------------------------------- |
| **Figma Link**      | <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=191-18871&t=DqqO5Kb23toIJC3i-4> |
| **Figma Component** | `section__header-search`                                                                              |

**Действия:** 

1. Ввести меньше 3х символов (ab) --> Поле ввода заполняется, ничего больше не происходит

2. Ввести больше 3х символов (abcd) --> Вызов GET `/products` с text=abcd

3. Ввод спецсимволов, пробелов, emoji, пустая строка --> Разрешен, Вызов GET `/products` с text= начиная с 3 символа

4. Нажать на Х --> Очищается поле поиска

5. Нажать «Отмена» --> Очищается поле поиска и отображается состояние *First Session для НАЗ или АЗ если нет данных, отображается состояние Search для АЗ*

\___\_

##### Секция "Частые симптомы"

\- **Figma Link:** <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=193-19608&t=DqqO5Kb23toIJC3i-4>

\- **Section Model**: [section__symptoms](./../../obschee/section__symptoms) 

\___\_

##### Секция "Подсказки"

|                     |                                                                                                       |
| ------------------- | ----------------------------------------------------------------------------------------------------- |
| **Figma Link**      | <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=191-21027&t=DqqO5Kb23toIJC3i-4> |
| **Figma Component** | `section__subtitle`                                                                                   |
| **Swagger Model**   | `GET /products/suggestions?searchQuery={input}`<br>`string Items[i]`<br>                              |

**Mapping:**

| Название элемента в Figma | Название элемента в Swagger |
| ------------------------- | --------------------------- |
| list of chips, text       | Items[i]                    |
Если items = []/nill/null --> секция не отображается

**Действия**:

1. Выбрать подсказку --> Вызов `GET /products?searchQuery={selected_subtitle}` и переход к состоянию Search Done

2. Ошибка на запрос или данные не пришли --> Блок не отображается

\___\_

##### Секция "Действующее вещество"

|                     |                                                                                                       |
| ------------------- | ----------------------------------------------------------------------------------------------------- |
| **Figma Link**      | <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=191-21027&t=DqqO5Kb23toIJC3i-4> |
| **Figma Component** | `section__hints`                                                                                      |
| **Swagger Model**   | `GET /products/suggestions?searchQuery={input}`<br>`Substanse.[i].name`<br>                           |

**Mapping:**

| Название элемента в Figma | Название элемента в Swagger |
| ------------------------- | --------------------------- |
| list of chips, text       | `Substanse.[i].name`        |
Если Substanse = []/nill/null --> секция не отображается

**Действия**:

1. Выбрать подсказку --> Вызов `GET /products?searchQuery={selected_hint}` и переход к состоянию Search Done

2. Ошибка на запрос или данные не пришли --> Блок не отображается

\___\_

##### Секция "Категории"

|                     |                                                                                                      |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| **Figma Link**      | <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=179-4277&t=AmUtsxxaRrtxBfUc-4> |
| **Figma Component** | `section__radio_list`                                                                                |
| **Swagger Model**   | `GET /user/purchases/categories`<br>`PurchaseCategory`<br>                                           |

**Mapping:**

| Название элемента в Figma | Название элемента в Swagger |
| ------------------------- | --------------------------- |
| list of radio, text       | PurchaseCategory.[i].name   |
Если PurchaseCategory = []/nill/null --> секция не отображается

**Действия**:

1. Выбрать категорию --> Вызов `GET /user/purchases?categoryId={PurchaseCategory.id}` для фильтрации покупок

2. Ошибка на запрос или данные не пришли --> Блок не отображается

\___\_

##### Секция "Последние покупки"

\- **Figma Link:** <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=193-7501&t=AmUtsxxaRrtxBfUc-4>

\- **Section Model**: [section__my-purchases](./../../obschee/section__my-purchases) (scroll = on, name = «Последние покупки», model = `purchasedProducts.[]`)

\___\_

##### Секция "Товары"

\- **Figma Link:** <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=193-19854&t=DqqO5Kb23toIJC3i-4>

\- **Section Model**: [section__catalog](./../../obschee/section__catalog) (state = small catalog, name = «Товары», model = `products.[]`)

\___\_

##### Секция "Результаты поиска"

\- **Figma Link:** <https://www.figma.com/design/nLDpIUh4gksHkJxWpdx5Jq/AI-Boost?node-id=193-19854&t=DqqO5Kb23toIJC3i-4>

\- **Section Model**: [section__catalog](./../../obschee/section__catalog) (state = catalog, name = «», model = `products.[]`)

## Стратегия загрузки данных

Все GET‑запросы выполняются параллельно. При новом вводе текста предыдущий вызов `/products` отменяется.

UI обновляется секциями по мере прихода данных (partial rendering).

## Стратегия возврата на экран

Сохраняем scroll‑позицию и текст запроса; выполняем повторный поиск, если прошло > 15 мин.

## Нюансы поведения и виджетов

-  Минимальная зона клика -- 44 × 44 pt.

-  Input history отображается, если `history.length > 0`.

## Side‑эффекты

-

## Edge‑cases & Validation

-

## Ограничения

-  Подсказки ограничены 20 элементами.

-  Каталог подгружается порциями по 20 позиций (пагинация).
</file>
