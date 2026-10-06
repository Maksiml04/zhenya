# Танцевально-спортивный центр «Форум» — статический сайт

Нео-минималистичный статический сайт танцевального центра.
Все тексты и изображения сохранены локально.
Вёрстка собственная (не копирует тему исходного сайта).

## Быстрый старт — GitHub Pages

```bash
# 1. Скопировать репозиторий
cd ~/PycharmProjects/zhenya

# 2. (Опционально) Указать домен для sitemap.xml
export SITE_URL="https://username.github.io/repo-name"

# 3. Пересобрать (если меняли домен)
python3 build.py

# 4. Залить на GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/username/repo-name.git
git push -u origin main
```

**В настройках репозитория** (GitHub → Settings → Pages):
- Source: **Deploy from a branch**
- Branch: `main`, folder: `/` (root)
- (Если у вас свой домен) укажите его в секции **Custom domain** — файл `CNAME` уже создан.

Сайт будет доступен по адресу `https://username.github.io/repo-name/`.

## Запуск локально

```bash
cd zhenya
python3 -m http.server 8000
# открыть http://localhost:8000/
```

## Пересборка

```bash
python3 build.py
# или с доменом: SITE_URL="https://forumdance.ru" python3 build.py
```

## Структура

```
zhenya/
├── build.py              # генератор (content.json → HTML, sitemap, robots)
├── content.json          # весь контент
├── css/style.css         # стили (нео-минимализм, 5 тем направлений)
├── js/main.js            # меню, модалки, формы, лайтбокс
├── img/logo.svg          # логотип
├── userfls/              # изображения (~195 МБ)
├── .nojekyll             # отключает Jekyll (нужно для GitHub Pages)
├── CNAME                 # домен (если свой)
├── nginx.conf            # конфиг для самостоятельного хостинга
├── index.html, 404.html, sitemap.xml, robots.txt
├── o-nas/ napravleniya-tantsev/ trenery/ nashi-dostizheniya/
├── photo/ video/ news/ kontakty/ privacy/
└── _migration_extract.py # разовый скрипт миграции
```

## 5 тем оформления направлений

| Направление | Тема | Hero |
|---|---|---|
| Спортивные бальные танцы | Красный, динамичный | Full-bleed изображение с оверлеем |
| Современные танцы | Фиолетовый, асимметрия | Сплит-экран (текст + изображение) |
| Танцы для детей | Оранжевый, дерзкий | Градиент + геометрические круги |
| Танцы для взрослых | Изумрудный, минимализм | Круглое фото, крупный шрифт |
| Свадебный танец | Розовый, воздушный | Мягкий градиент, центрирование |

## Что редактировать

- **Тексты/списки** — `content.json` (затем `python3 build.py`).
- **Домен** — `SITE_URL` в `build.py` или через `export SITE_URL=...`.
- **Цвета/оформление** — CSS-переменные `:root` и `[data-theme=...]` в `css/style.css`.
- **Отправка форм** — сейчас демо-режим. Подключите бэкенд в `js/main.js` (замените `setTimeout` на `fetch` к вашему API).
- **Изображения** — положите новые в `userfls/...` и обновите пути в `content.json`.

## О внешних встраиваниях

Живые сервисы (нельзя «скачать на диск»):
- **Видео** — YouTube (iframe embed).
- **Карта** — Яндекс.Карты (iframe embed).
- **Соцсети** — ссылки на Instagram и ВКонтакте.

Замените при необходимости в `content.json`.
