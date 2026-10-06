#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор статического сайта танцевально-спортивного центра «Форум».

Данные: content.json (извлекается миграционным скриптом из сохранённых страниц).
Вёрстка/стили/скрипты — собственные (css/style.css, js/main.js).
Все внутренние ссылки и изображения — локальные (относительные), без обращений
к внешнему хосту. Сторонние встраивания (YouTube, Яндекс.Карта) и профили
соцсетей оставлены как есть — это внешние сервисы, а не файлы сайта.

Запуск:  python3 build.py
Просмотр: python3 -m http.server 8000  ->  http://localhost:8000/
"""
import os
import re
import json
import html
import math

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(ROOT, "content.json"), encoding="utf-8"))

# Домен для sitemap.xml / robots.txt
# Для GitHub Pages укажите: https://USERNAME.github.io/zhenya
# Можно задать через переменную окружения SITE_URL
SITE_URL = os.environ.get("SITE_URL", "https://USERNAME.github.io/zhenya")

SITE = DATA["site"]
BRAND = SITE["brand_name"]
CTYPE = SITE["brand_type"]
C = SITE["contacts"]
SOCIALS = C.get("socials", [])
PROMO = SITE.get("promo", {})
NAV = DATA["nav"]
DIRECTIONS = DATA["directions"]
TRAINERS = DATA["trainers"]
ACHIEVEMENTS = DATA["achievements"]
NEWS = DATA["news"]
PHOTOS = DATA["photos"]
VIDEOS = DATA["videos"]

NEWS_PAGE_SIZE = 20

# Маппинг тем оформления для направлений
DIRECTION_THEMES = {
    "cportivnye-tantsy": "sport",
    "sovremennye-tantsy": "modern",
    "tantsy-dlya-detey": "kids",
    "tantsy-dlya-vzroslykh": "adults",
    "svadebnyy-tanets": "wedding",
}


# ============================================================================
# Утилиты
# ============================================================================
def esc(s):
    return html.escape(str(s if s is not None else ""), quote=False)


def eattr(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def write(path, content):
    full = os.path.join(ROOT, path)
    d = os.path.dirname(full)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def home_href(base):
    return base if base else "./"


def base_img(base, path):
    return (base + path.lstrip("/")) if path else ""


def fill_tokens(s, base):
    if not s:
        return ""
    return s.replace("{{BASE}}", base).replace("{{HOME}}", home_href(base))


def strip_tags(s):
    s = html.unescape(str(s or ""))
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def excerpt(body_html, n=150):
    t = strip_tags(body_html)
    if len(t) <= n:
        return t
    return t[:n].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def clean_desc(title, desc):
    d = strip_tags(desc)
    if title and d.startswith(title):
        d = d[len(title):].strip()
    return d


def nav_url(u):
    return (u + "/") if u else None


# ============================================================================
# Иконки
# ============================================================================
def icon_social(kind):
    if kind == "vk":
        return ('<svg viewBox="0 0 24 24" aria-hidden="true"><text x="12" y="16.5" '
                'text-anchor="middle" font-family="Arial, sans-serif" font-size="10" '
                'font-weight="700" fill="currentColor">VK</text></svg>')
    if kind in ("insta", "instagram"):
        return ('<svg viewBox="0 0 24 24" aria-hidden="true">'
                '<rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="2"/>'
                '<circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/>'
                '<circle cx="17.4" cy="6.6" r="1.3" fill="currentColor"/></svg>')
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/></svg>'


CONTACT_ICONS = {
    "pin": '<path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11z"/><circle cx="12" cy="10" r="2.6"/>',
    "phone": '<path d="M4 4h4l2 5-2.4 1.4a12 12 0 0 0 6 6L15 14l5 2v4a1 1 0 0 1-1 1A16 16 0 0 1 3 5a1 1 0 0 1 1-1z"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5.2l3.2 2"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 7l8.5 6 8.5-6"/>',
}


def icon_contact(kind):
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{CONTACT_ICONS[kind]}</svg>'


def socials_html():
    return "".join(
        f'<a class="social" href="{eattr(s["url"])}" target="_blank" rel="noopener" '
        f'aria-label="{eattr(s["name"])}">{icon_social(s.get("icon"))}</a>'
        for s in SOCIALS
    )


# ============================================================================
# Навигация / шапка / подвал
# ============================================================================
def _active(item, active_url):
    if not active_url:
        return False
    u = nav_url(item.get("url"))
    if u and active_url.startswith(u):
        return True
    for ch in item.get("children", []):
        cu = nav_url(ch.get("url"))
        if cu and active_url.startswith(cu):
            return True
    return False


def render_nav(base, active_url):
    items = []
    for item in NAV:
        active = _active(item, active_url)
        has_kids = bool(item.get("children"))
        cls = "nav__item" + (" has-children" if has_kids else "") + (" is-active" if active else "")
        href = (base + nav_url(item["url"])) if item.get("url") else "#"
        caret = '<i class="nav__caret"></i>' if has_kids else ""
        link = f'<a class="nav__link" href="{href}">{esc(item["title"])}{caret}</a>'
        if has_kids:
            subs = []
            for ch in item["children"]:
                cu = nav_url(ch.get("url"))
                ch_active = bool(active_url) and cu and active_url.startswith(cu)
                ch_cls = ' class="is-active"' if ch_active else ""
                subs.append(f'<li><a href="{base}{cu}"{ch_cls}>{esc(ch["title"])}</a></li>')
            link += f'<ul class="nav__dropdown">{"".join(subs)}</ul>'
        items.append(f'<li class="{cls}">{link}</li>')
    return f'<ul class="nav__list">{"".join(items)}</ul>'


def render_topbar(base):
    return f"""
<div class="topbar">
  <div class="container">
    <div class="topbar__addr">{icon_contact("pin")} <span>{esc(C.get("address_top"))} &nbsp;•&nbsp; {esc(C.get("hours"))}</span></div>
    <div class="topbar__addr"><a href="tel:{eattr(C.get("phone_raw"))}">{esc(C.get("phone_display"))}</a></div>
    <div class="topbar__socials">{socials_html()}</div>
  </div>
</div>"""


def render_header(base, active_url):
    home = home_href(base)
    return f"""
<header class="header">
  <div class="container header__inner">
    <a class="brand" href="{home}">
      <img src="{base}img/logo.svg" alt="Логотип {esc(BRAND)}">
      <span class="brand__text">
        <span class="brand__name">«{esc(BRAND)}»</span>
        <span class="brand__type">{esc(CTYPE)}</span>
      </span>
    </a>
    <nav class="nav" aria-label="Основная навигация">
      {render_nav(base, active_url)}
      <div class="nav__mobile-cta">
        <a class="btn btn--solid btn--sm" href="{base}kontakty/">Записаться</a>
      </div>
    </nav>
    <div class="header__cta">
      <div class="header__phone">
        <a href="tel:{eattr(C.get("phone_raw"))}">{esc(C.get("phone_display"))}</a>
        <span>{esc(C.get("phone_note"))}</span>
      </div>
      <button class="btn btn--solid btn--sm" data-modal-open="callback">Заказать звонок</button>
      <button class="burger" aria-label="Меню" aria-expanded="false"><span></span></button>
    </div>
  </div>
</header>
<div class="nav-backdrop"></div>"""


def render_footer(base):
    home = home_href(base)
    menu = []
    for item in NAV:
        if item.get("url"):
            menu.append(f'<li><a href="{base}{nav_url(item["url"])}">{esc(item["title"])}</a></li>')
        for ch in item.get("children", []):
            menu.append(f'<li><a href="{base}{nav_url(ch["url"])}">{esc(ch["title"])}</a></li>')
    dirs = "".join(
        f'<li><a href="{base}{d["route"]}/">{esc(d["title"])}</a></li>'
        for d in DIRECTIONS["items"]
    )
    return f"""
<footer class="footer">
  <div class="container">
    <div class="footer__grid">
      <div>
        <a class="brand" href="{home}">
          <img src="{base}img/logo.svg" alt="{esc(BRAND)}">
          <span class="brand__text">
            <span class="brand__name">«{esc(BRAND)}»</span>
            <span class="brand__type">{esc(CTYPE)}</span>
          </span>
        </a>
        <p class="footer__about">{esc(CTYPE)} «{esc(BRAND)}» — спортивные бальные и современные
        танцы для детей и взрослых. Более 30 лет на паркете.</p>
        <div class="footer__socials">{socials_html()}</div>
      </div>
      <div>
        <h4>Меню</h4>
        <ul class="footer__menu">{"".join(menu)}</ul>
      </div>
      <div>
        <h4>Направления</h4>
        <ul class="footer__menu">{dirs}</ul>
      </div>
      <div>
        <h4>Контакты</h4>
        <ul class="footer__contacts">
          <li>{icon_contact("pin")} <span>{esc(C.get("address"))}</span></li>
          <li>{icon_contact("phone")} <a href="tel:{eattr(C.get("phone_raw"))}">{esc(C.get("phone_display"))}</a></li>
          <li>{icon_contact("clock")} <span>{esc(C.get("hours"))}</span></li>
        </ul>
      </div>
    </div>
    <div class="footer__bottom">
      <div>© <span id="year">2026</span> «{esc(BRAND)}». Танцевальная школа.</div>
      <div><a href="{base}privacy/">Политика конфиденциальности</a></div>
    </div>
  </div>
</footer>"""


# ============================================================================
# Формы / модалки
# ============================================================================
FORM_DIRECTIONS = [d["title"] for d in DIRECTIONS["items"]]


def captcha_html(uid):
    return f"""
<div class="captcha">
  <input type="checkbox" name="robot" id="robot-{uid}" required>
  <label for="robot-{uid}">Я не робот</label>
  <div class="captcha__brand">защита<br>от спама</div>
</div>"""


def agree_html(base):
    return f"""
<div class="form-note">
  <label class="agree">
    <input type="checkbox" name="agree" required>
    <span>Отправляя форму, я даю согласие на
    <a href="{base}privacy/">обработку персональных данных</a>.</span>
  </label>
</div>"""


def form_success(title="Заявка отправлена!"):
    return f"""
<div class="form-success">
  <div class="check">✓</div>
  <h3>{esc(title)}</h3>
  <p>Наш менеджер свяжется с вами в течение 10 минут.</p>
</div>"""


def signup_form(base, uid):
    opts = "".join(f'<option value="{eattr(o)}">{esc(o)}</option>' for o in FORM_DIRECTIONS)
    return f"""
<form data-form novalidate>
  <div class="field">
    <label for="dir-{uid}">Направление</label>
    <select id="dir-{uid}" name="direction" required>
      <option value="">Выберите направление</option>
      {opts}
    </select>
  </div>
  <div class="field">
    <label for="name-{uid}">Ваше имя *</label>
    <input id="name-{uid}" type="text" name="name" placeholder="Имя" required>
  </div>
  <div class="field">
    <label for="phone-{uid}">Телефон *</label>
    <input id="phone-{uid}" type="tel" name="phone" placeholder="+7 (___) ___-__-__" required>
  </div>
  {captcha_html(uid)}
  <button class="btn btn--light" type="submit" style="width:100%">Отправить заявку</button>
  {agree_html(base)}
</form>"""


def render_signup(base, uid="s1"):
    return f"""
<div class="signup form-wrap">
  <h3>Онлайн-запись</h3>
  <p>Оставьте заявку — подберём группу и удобное время.</p>
  {signup_form(base, uid)}
  {form_success("Вы записаны!")}
</div>"""


def render_modals(base):
    return f"""
<div class="modal" id="callback" role="dialog" aria-modal="true" aria-labelledby="cb-title">
  <div class="modal__overlay"></div>
  <div class="modal__box">
    <button class="modal__close" aria-label="Закрыть">×</button>
    <h3 id="cb-title">Заказать звонок</h3>
    <p class="sub">Оставьте номер — перезвоним в течение 10 минут.</p>
    <div class="form-wrap">
      <form data-form novalidate>
        <div class="field">
          <label for="cb-name">Ваше имя *</label>
          <input id="cb-name" type="text" name="name" placeholder="Имя" required>
        </div>
        <div class="field">
          <label for="cb-phone">Телефон *</label>
          <input id="cb-phone" type="tel" name="phone" placeholder="+7 (___) ___-__-__" required>
        </div>
        {captcha_html("cb")}
        <button class="btn btn--solid" type="submit" style="width:100%">Перезвоните мне</button>
        {agree_html(base)}
      </form>
      {form_success("Спасибо!")}
    </div>
  </div>
</div>
<div class="lightbox" role="dialog" aria-modal="true" aria-label="Просмотр фото">
  <button class="lightbox__close" aria-label="Закрыть">×</button>
  <img src="" alt="">
  <div class="lightbox__cap"></div>
</div>"""


# ============================================================================
# Каркас
# ============================================================================
def layout(title, base, body, active_url="", meta_desc=None, og=None):
    desc = meta_desc or f'{CTYPE} «{BRAND}» — {esc(C.get("address_top"))}. {esc(C.get("phone_display"))}.'
    full_title = f"{title} — {CTYPE} «{BRAND}»" if title else f'{CTYPE} «{BRAND}»'
    og = og or {}
    og_title = esc(og.get("title") or full_title)
    og_desc = esc(og.get("description") or desc)
    og_type = esc(og.get("type") or "website")
    og_img = esc(og.get("image") or "")
    og_img_tag = f'<meta property="og:image" content="{og_img}">' if og_img else ""
    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "DanceSchool",
        "name": f'{CTYPE} «{BRAND}»',
        "telephone": C.get("phone_raw"),
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Москва",
            "streetAddress": C.get("address_top"),
            "addressCountry": "RU",
        },
    }, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{eattr(desc)}">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_desc}">
<meta property="og:type" content="{og_type}">
{og_img_tag}
<link rel="icon" href="{base}img/logo.svg" type="image/svg+xml">
<link rel="stylesheet" href="{base}css/style.css">
<script type="application/ld+json">{jsonld}</script>
</head>
<body>
{render_topbar(base)}
{render_header(base, active_url)}
<main id="main">
{body}
</main>
{render_footer(base)}
<button class="to-top" aria-label="Наверх">↑</button>
{render_modals(base)}
<script src="{base}js/main.js"></script>
</body>
</html>
"""


def page_head(base, title, trail):
    crumbs = [f'<a href="{home_href(base)}">Главная</a>']
    for label, url in trail:
        crumbs.append('<span>/</span>')
        if url:
            crumbs.append(f'<a href="{base}{url}">{esc(label)}</a>')
        else:
            crumbs.append(f'<span>{esc(label)}</span>')
    return f"""
<section class="page-head">
  <div class="container">
    <h1>{esc(title)}</h1>
    <nav class="breadcrumbs" aria-label="Хлебные крошки">{"".join(crumbs)}</nav>
  </div>
</section>"""


def gallery_html(base, items, cap_prefix=""):
    if not items:
        return ""
    figs = []
    for g in items:
        cap = eattr(g.get("title") or cap_prefix)
        figs.append(
            f'<figure class="gallery__item zoomable" data-full="{base}{g["full"]}" data-caption="{cap}">'
            f'<img src="{base}{g["thumb"]}" alt="{cap}" loading="lazy">'
            f'<figcaption class="gallery__cap">{esc(g.get("title") or "Фото")}</figcaption></figure>'
        )
    return f'<div class="gallery">{"".join(figs)}</div>'


# ============================================================================
# Карточки
# ============================================================================
def direction_card(base, it):
    url = f'{base}{it["route"]}/'
    desc = clean_desc(it["title"], it.get("desc"))
    return f"""
<article class="card reveal">
  <a class="card__media" href="{url}"><img src="{base}{it["thumb"]}" alt="{eattr(it["title"])}" loading="lazy"></a>
  <div class="card__body">
    <h3 class="card__title"><a href="{url}">{esc(it["title"])}</a></h3>
    <p class="card__text">{esc(excerpt(desc, 120))}</p>
    <a class="card__more" href="{url}">Подробнее</a>
  </div>
</article>"""


def news_card(base, it):
    url = f'{base}{it["route"]}/'
    det = NEWS["details"].get(it["slug"], {})
    ex = excerpt(det.get("body_html", ""), 120)
    return f"""
<article class="card news-card reveal">
  <a class="card__media" href="{url}"><img src="{base}{it["thumb"]}" alt="{eattr(it["title"])}" loading="lazy"></a>
  <div class="card__body">
    <span class="news-card__date">{esc(it.get("date"))}</span>
    <h3 class="card__title"><a href="{url}">{esc(it["title"])}</a></h3>
    <p class="card__text">{esc(ex)}</p>
    <a class="card__more" href="{url}">Подробнее</a>
  </div>
</article>"""


def coach_card(base, it):
    url = f'{base}{it["route"]}/'
    return f"""
<article class="card reveal">
  <a class="card__media card__media--coach" href="{url}"><img src="{base}{it["thumb"]}" alt="{eattr(it["name"])}" loading="lazy"></a>
  <div class="card__body">
    <h3 class="card__title"><a href="{url}">{esc(it["name"])}</a></h3>
    <div class="coach__role">{esc(it.get("role"))}</div>
    <a class="card__more coach__more" href="{url}">Подробнее</a>
  </div>
</article>"""


def achievement_card(base, it):
    url = f'{base}{it["route"]}/'
    return (f'<a class="achv reveal" href="{url}"><img src="{base}{it["thumb"]}" '
            f'alt="{eattr(it["title"])}" loading="lazy">'
            f'<span class="achv__caption">{esc(it["title"])} ›</span></a>')


# ============================================================================
# Страница-деталь (универсальная)
# ============================================================================
def detail_body(base, title, body_html, gallery):
    lead = ""
    rest = gallery or []
    if rest:
        g0 = rest[0]
        lead = (f'<figure class="lead-img zoomable" data-full="{base}{g0["full"]}" data-caption="{eattr(title)}">'
                f'<img src="{base}{g0["thumb"]}" alt="{eattr(title)}"></figure>')
        rest = rest[1:]
    gal = gallery_html(base, rest, title)
    return lead + fill_tokens(body_html, base) + gal


def detail_page(base, title, trail, body_html, gallery, uid):
    return f"""
{page_head(base, title, trail)}
<section class="page-body">
  <div class="container layout-2">
    <div class="prose reveal">{detail_body(base, title, body_html, gallery)}</div>
    <aside class="aside-sticky reveal">{render_signup(base, uid)}</aside>
  </div>
</section>
"""


# ============================================================================
# Страницы
# ============================================================================
def page_home(base):
    hero_img = (PHOTOS[0]["thumb"] if PHOTOS else DIRECTIONS["items"][0]["thumb"])
    about_img = (PHOTOS[1]["thumb"] if len(PHOTOS) > 1 else DIRECTIONS["items"][-1]["thumb"])
    dirs = "".join(direction_card(base, d) for d in DIRECTIONS["items"][:4])
    news = "".join(news_card(base, n) for n in NEWS["items"][:3])
    achs = "".join(achievement_card(base, a) for a in ACHIEVEMENTS["items"])
    n_trainers = len(TRAINERS["items"])
    n_dirs = len(DIRECTIONS["items"])
    promo_text = PROMO.get("text_html", "")
    promo_btn = PROMO.get("button", "Записаться онлайн")
    promo_url = PROMO.get("url", "kontakty/")
    return f"""
<section class="hero">
  <div class="container hero__inner">
    <div class="hero__content reveal">
      <span class="hero__eyebrow">Спортивные бальные и современные танцы</span>
      <h1>{esc(CTYPE)} <em>«{esc(BRAND)}»</em></h1>
      <p class="hero__lead">Более 30 лет обучаем танцам детей и взрослых. Профессиональные
      тренеры и судьи, групповые и индивидуальные занятия, выступления и соревнования.</p>
      <div class="hero__actions">
        <a class="btn btn--solid" href="{base}kontakty/">Записаться онлайн</a>
        <a class="btn btn--outline" href="{base}napravleniya-tantsev/">Направления</a>
      </div>
      <div class="hero__stats">
        <div class="hero__stat"><b>30+</b><span>лет опыта</span></div>
        <div class="hero__stat"><b>{n_dirs}</b><span>направлений</span></div>
        <div class="hero__stat"><b>{n_trainers}</b><span>тренеров</span></div>
      </div>
    </div>
    <div class="hero__art reveal"><img src="{base}{hero_img}" alt="Танцевально-спортивный центр «{esc(BRAND)}»"></div>
  </div>
</section>

<section class="season">
  <div class="container">
    <div class="season__text">{promo_text}</div>
      <a class="btn btn--solid" href="{base}{promo_url}">{esc(promo_btn)}</a>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head">
      <h2 class="title-line">Направления танцев</h2>
    </div>
    <div class="grid grid--4">{dirs}</div>
    <div style="text-align:center;margin-top:34px">
      <a class="btn btn--outline" href="{base}napravleniya-tantsev/">Все направления</a>
    </div>
  </div>
</section>

<section class="section" style="background:#fff">
  <div class="container about">
    <div class="about__media reveal">
      <img src="{base}{about_img}" alt="О центре «{esc(BRAND)}»">
      <div class="about__badge"><b>30+</b><span>лет на паркете</span></div>
    </div>
    <div class="about__text reveal">
      <h2 class="title-line title-line--left">О нас</h2>
      {fill_tokens(DATA.get("home_about_html", ""), base)}
      <a class="btn btn--outline" href="{base}o-nas/">Подробнее</a>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head"><h2 class="title-line">Новости</h2></div>
    <div class="grid grid--3">{news}</div>
    <div style="text-align:center;margin-top:30px">
      <a class="btn btn--outline" href="{base}news/">Все новости</a>
    </div>
  </div>
</section>

<section class="section" style="background:#fff">
  <div class="container">
    <div class="section-head"><h2 class="title-line">Наши достижения</h2></div>
    <div class="grid grid--3">{achs}</div>
  </div>
</section>

<section class="section">
  <div class="container contact-grid">
    <div class="reveal">
      <h2 class="title-line title-line--left">Контакты</h2>
      <ul class="contact-list">
        <li><span class="ico">{icon_contact("pin")}</span><span><b>Адрес</b><span class="v">{esc(C.get("address"))}</span></span></li>
        <li><span class="ico">{icon_contact("phone")}</span><span><b>Телефон</b><a href="tel:{eattr(C.get("phone_raw"))}">{esc(C.get("phone_display"))}</a> <span class="v">({esc(C.get("phone_note"))})</span></span></li>
        <li><span class="ico">{icon_contact("clock")}</span><span><b>Часы работы</b><span class="v">{esc(C.get("hours"))}</span></span></li>
      </ul>
      <div class="footer__socials" style="margin-top:8px">{socials_html()}</div>
    </div>
    <div class="reveal">{render_signup(base, "home")}</div>
  </div>
</section>
"""


def page_about(base):
    return f"""
{page_head(base, "О компании", [("О компании", None)])}
<section class="page-body">
  <div class="container layout-2">
    <div class="prose reveal">{fill_tokens(DATA.get("about_html", ""), base)}</div>
    <aside class="aside-sticky reveal">{render_signup(base, "about")}</aside>
  </div>
</section>
"""


def page_directions_list(base):
    rows = []
    for d in DIRECTIONS["items"]:
        url = f'{base}{d["route"]}/'
        desc = clean_desc(d["title"], d.get("desc"))
        rows.append(f"""
<article class="dir-row reveal">
  <a class="dir-row__media" href="{url}"><img src="{base}{d["thumb"]}" alt="{eattr(d["title"])}" loading="lazy"></a>
  <div class="dir-row__body">
    <h3>{esc(d["title"])}</h3>
    <p>{esc(excerpt(desc, 320))}</p>
    <a class="card__more" href="{url}">Подробнее</a>
  </div>
</article>""")
    return f"""
{page_head(base, "Направления танцев", [("Направления танцев", None)])}
<section class="page-body">
  <div class="container layout-2">
    <div>{"".join(rows)}</div>
    <aside class="aside-sticky reveal">{render_signup(base, "dir")}</aside>
  </div>
</section>
"""


def page_trainers_list(base):
    cards = "".join(coach_card(base, t) for t in TRAINERS["items"])
    return f"""
{page_head(base, "Тренеры", [("Тренеры", None)])}
<section class="page-body">
  <div class="container">
    <div class="section-head"><p>Профессиональные тренеры-преподаватели центра «{esc(BRAND)}».</p></div>
    <div class="grid grid--3">{cards}</div>
    <div style="max-width:420px;margin:40px auto 0" class="reveal">{render_signup(base, "coach")}</div>
  </div>
</section>
"""


def page_achievements_list(base):
    cards = "".join(achievement_card(base, a) for a in ACHIEVEMENTS["items"])
    return f"""
{page_head(base, "Наши достижения", [("Наши достижения", None)])}
<section class="page-body">
  <div class="container">
    <div class="grid grid--3">{cards}</div>
  </div>
</section>
"""


def page_photo(base):
    return f"""
{page_head(base, "Фотогалерея", [("Фотогалерея", None)])}
<section class="page-body">
  <div class="container">
    {gallery_html(base, PHOTOS)}
  </div>
</section>
"""


def page_video(base):
    vids = [v["embed"] for v in VIDEOS
            if any(k in v["embed"] for k in ("youtube", "youtu.be", "vimeo"))]
    if not vids:
        vids = [v["embed"] for v in VIDEOS]
    cards = "".join(
        f'<div class="video-embed reveal"><iframe src="{eattr(src)}" title="Видео" '
        f'loading="lazy" allow="autoplay; encrypted-media; fullscreen" allowfullscreen></iframe></div>'
        for src in vids
    )
    return f"""
{page_head(base, "Видео", [("Видео", None)])}
<section class="page-body">
  <div class="container">
    <div class="grid grid--2">{cards}</div>
  </div>
</section>
"""


def pager_html(base, page_no, total):
    if total <= 1:
        return ""
    def link(p, label=None, cls=""):
        if p == 1:
            href = f"{base}news/"
        else:
            href = f"{base}news/page{p}/"
        return f'<a class="{cls}" href="{href}">{label or p}</a>'
    cells = []
    if page_no > 1:
        cells.append(link(page_no - 1, "‹", "prev"))
    window = set([1, total, page_no, page_no - 1, page_no + 1, page_no - 2, page_no + 2])
    last = 0
    for p in sorted(x for x in window if 1 <= x <= total):
        if last and p - last > 1:
            cells.append('<span class="dots">…</span>')
        if p == page_no:
            cells.append(f'<span class="current">{p}</span>')
        else:
            cells.append(link(p))
        last = p
    if page_no < total:
        cells.append(link(page_no + 1, "›", "next"))
    return f'<nav class="pager">{"".join(cells)}</nav>'


def page_news_list(base, page_items, page_no, total):
    cards = "".join(news_card(base, n) for n in page_items)
    return f"""
{page_head(base, "Новости", [("Новости", None)])}
<section class="page-body">
  <div class="container">
    <div class="grid grid--3">{cards}</div>
    {pager_html(base, page_no, total)}
  </div>
</section>
"""


def page_news_detail(base, it):
    det = NEWS["details"].get(it["slug"], {})
    head = page_head(base, it["title"], [("Новости", "news/"), (it["title"], None)])
    date_badge = f'<span class="news-card__date">{esc(it.get("date"))}</span>' if it.get("date") else ""
    body = detail_body(base, it["title"], det.get("body_html", ""), det.get("gallery", []))
    return f"""
{head}
<section class="page-body">
  <div class="container layout-2">
    <div class="prose reveal">{date_badge}{body}</div>
    <aside class="aside-sticky reveal">{render_signup(base, "news")}</aside>
  </div>
</section>
"""


def page_contacts(base):
    map_iframe = C.get("map_iframe", "")
    map_block = (f'<div class="map"><iframe title="Карта" loading="lazy" src="{eattr(map_iframe)}"></iframe></div>'
                 if map_iframe else "")
    return f"""
{page_head(base, "Контакты", [("Контакты", None)])}
<section class="page-body">
  <div class="container">
    <div class="contact-grid">
      <div class="reveal">
        <h2 class="title-line title-line--left">Как с нами связаться</h2>
        <ul class="contact-list">
          <li><span class="ico">{icon_contact("pin")}</span><span><b>Адрес</b><span class="v">{esc(C.get("address"))}</span></span></li>
          <li><span class="ico">{icon_contact("phone")}</span><span><b>Телефон</b><a href="tel:{eattr(C.get("phone_raw"))}">{esc(C.get("phone_display"))}</a> <span class="v">({esc(C.get("phone_note"))})</span></span></li>
          <li><span class="ico">{icon_contact("clock")}</span><span><b>Часы работы</b><span class="v">{esc(C.get("hours"))}</span></span></li>
        </ul>
        <h3 style="margin-top:10px">Мы в соцсетях</h3>
        <div class="footer__socials">{socials_html()}</div>
        {map_block}
      </div>
      <div class="reveal">{render_signup(base, "contact")}</div>
    </div>
  </div>
</section>
"""


def page_privacy(base):
    return f"""
{page_head(base, "Согласие на обработку персональных данных", [("Политика конфиденциальности", None)])}
<section class="page-body">
  <div class="container">
    <div class="prose reveal">{fill_tokens(DATA.get("privacy_html", ""), base)}</div>
  </div>
</section>
"""


def page_404(base):
    return f"""
<section class="page-head"><div class="container"><h1>Страница не найдена</h1>
<nav class="breadcrumbs"><a href="{home_href(base)}">Главная</a><span>/</span><span>404</span></nav></div></section>
<section class="page-body"><div class="container" style="text-align:center">
<p style="font-size:1.1rem;color:var(--muted);max-width:520px;margin:0 auto 24px">
К сожалению, запрошенная страница не существует. Перейдите на главную или выберите раздел в меню.</p>
<a class="btn btn--solid" href="{home_href(base)}">На главную</a>
</div></section>
"""


# ============================================================================
# Hero для направлений (5 уникальных оформлений)
# ============================================================================
def dir_hero_html(base, it, det, theme):
    """Создаёт уникальную Hero-секцию для страницы направления."""
    hero_img = (det.get("gallery", [{}])[0].get("thumb", "")
                if det.get("gallery") else it.get("thumb", ""))
    title = it["title"]
    lead = it.get("desc", "")
    lead = excerpt(lead, 280) if lead else ""
    btn = f'<a class="btn btn--solid btn--sm" href="#content">{esc("Подробнее")}</a>'

    # --- Sport: мощный, тёмный фон с изображением ---
    if theme == "sport":
        return f"""
<section class="dir-hero" data-theme="sport">
  <div class="dir-hero__bg"><img src="{base}{hero_img}" alt="" loading="lazy"></div>
  <div class="dir-hero__inner">
    <h1 class="dir-hero__title">{esc(title)}</h1>
    <p class="dir-hero__text">{esc(lead)}</p>
    <div class="dir-hero__stats">
      <div><b>30+</b><span>лет традиций</span></div>
      <div><b>2</b><span>программы</span></div>
      <div><b>5</b><span>танцев каждой</span></div>
    </div>
    <a class="btn btn--light" href="#content">Подробнее</a>
  </div>
</section>"""

    # --- Modern: сплит-экран, изображение справа ---
    if theme == "modern":
        return f"""
<section class="dir-hero" data-theme="modern">
  <div class="dir-hero__inner">
    <h1 class="dir-hero__title">{esc(title)}</h1>
    <p class="dir-hero__text">{esc(lead)}</p>
    <a class="btn btn--solid dir-hero__btn" href="#content">Подробнее</a>
    <div class="dir-hero__visual"><img src="{base}{hero_img}" alt="" loading="lazy"></div>
  </div>
</section>"""

    # --- Kids: яркий градиент, круги, центрировано ---
    if theme == "kids":
        return f"""
<section class="dir-hero" data-theme="kids">
  <div class="dir-hero__deco"><span></span><span></span><span></span></div>
  <div class="dir-hero__inner" style="position:relative;z-index:2">
    <h1 class="dir-hero__title">{esc(title)}</h1>
    <p class="dir-hero__text">{esc(lead)}</p>
    <a class="btn btn--solid" href="#content">Подробнее</a>
  </div>
</section>"""

    # --- Adults: минимализм, круглая фотография справа ---
    if theme == "adults":
        return f"""
<section class="dir-hero" data-theme="adults">
  <div class="dir-hero__inner">
    <div class="dir-hero__info">
      <h1 class="dir-hero__title">{esc(title)}</h1>
      <p class="dir-hero__text">{esc(lead)}</p>
      <a class="btn btn--outline" href="#content">Подробнее</a>
    </div>
    <div class="dir-hero__img"><img src="{base}{hero_img}" alt="" loading="lazy"></div>
  </div>
</section>"""

    # --- Wedding: воздушный, градиент, центрировано ---
    if theme == "wedding":
        return f"""
<section class="dir-hero" data-theme="wedding">
  <div class="dir-hero__inner">
    <h1 class="dir-hero__title">{esc(title)}</h1>
    <p class="dir-hero__text">{esc(lead)}</p>
    <a class="btn btn--solid" href="#content">Подробнее</a>
  </div>
</section>"""

    return ""


# ============================================================================
# sitemap / robots
# ============================================================================
def build_sitemap(all_routes):
    seen = set()
    urls = []
    for r in all_routes:
        if r in seen:
            continue
        seen.add(r)
        loc = SITE_URL.rstrip("/") + "/" + r.lstrip("/")
        urls.append(f"  <url><loc>{esc(loc)}</loc></url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls) + "\n</urlset>\n")


def build_robots():
    return (f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL.rstrip('/')}/sitemap.xml\n")


# ============================================================================
# Сборка
# ============================================================================
def build():
    pages = []      # (out_path, title, active_url, body, meta_desc, og)
    routes = set()  # для sitemap

    def add(out, title, active, body, meta_desc=None, og=None):
        pages.append((out, title, active, body, meta_desc, og))
        r = os.path.dirname(out)
        route = (r + "/") if r else ""
        if route != "404/":
            routes.add(route)

    # Главная
    add("index.html", "", "", page_home(""))
    # О компании
    add("o-nas/index.html", "О компании", "o-nas/", page_about("../"))
    # Направления
    add("napravleniya-tantsev/index.html", "Направления танцев", "napravleniya-tantsev/",
        page_directions_list("../"))
    for d in DIRECTIONS["items"]:
        det = DIRECTIONS["details"].get(d["slug"], {})
        theme = DIRECTION_THEMES.get(d["slug"], "")
        out = f'{d["route"]}/index.html'
        b = "../../"
        hero = dir_hero_html(b, d, det, theme) if theme else ""
        body_html = det.get("body_html", "")
        gallery = det.get("gallery", [])
        trail = [("Направления танцев", "napravleniya-tantsev/"), (d["title"], None)]
        desc = excerpt(d.get("desc", "") or body_html, 160)
        og_img = (gallery[0]["thumb"] if gallery
                  else d["thumb"]) if d.get("thumb") else ""
        body = f"""{hero}
<section class="page-body" id="content">
  <div class="container layout-2">
    <div class="prose reveal">{detail_body(b, d["title"], body_html, gallery)}</div>
    <aside class="aside-sticky reveal">{render_signup(b, "d" + d["slug"][:4])}</aside>
  </div>
</section>"""
        add(out, d["title"], d["route"] + "/", body, desc,
            {"title": d["title"], "description": desc,
             "image": SITE_URL.rstrip("/") + "/" + og_img if og_img else "",
             "type": "website"})
    # Тренеры
    add("trenery/index.html", "Тренеры", "trenery/", page_trainers_list("../"))
    for t in TRAINERS["items"]:
        det = TRAINERS["details"].get(t["slug"], {})
        out = f'{t["route"]}/index.html'
        b = "../../"
        trail = [("Тренеры", "trenery/"), (t["name"], None)]
        desc = excerpt(det.get("body_html", ""), 160)
        body = detail_page(b, t["name"], trail,
                           det.get("body_html", ""), det.get("gallery", []), "t" + t["slug"][:4])
        add(out, t["name"], t["route"] + "/", body, desc,
            {"title": t["name"], "description": desc,
             "image": SITE_URL.rstrip("/") + "/" + t["thumb"] if t.get("thumb") else "",
             "type": "profile"})
    # Достижения
    add("nashi-dostizheniya/index.html", "Наши достижения", "nashi-dostizheniya/",
        page_achievements_list("../"))
    for a in ACHIEVEMENTS["items"]:
        det = ACHIEVEMENTS["details"].get(a["slug"], {})
        out = f'{a["route"]}/index.html'
        b = "../../"
        trail = [("Наши достижения", "nashi-dostizheniya/"), (a["title"], None)]
        body = detail_page(b, a["title"], trail,
                           det.get("body_html", ""), det.get("gallery", []), "a" + a["slug"][:4])
        add(out, a["title"], a["route"] + "/", body)
    # Фото / Видео
    add("photo/index.html", "Фотогалерея", "photo/", page_photo("../"))
    add("video/index.html", "Видео", "video/", page_video("../"))
    # Новости: список с пагинацией
    items = NEWS["items"]
    total = max(1, math.ceil(len(items) / NEWS_PAGE_SIZE))
    for p in range(total):
        chunk = items[p * NEWS_PAGE_SIZE:(p + 1) * NEWS_PAGE_SIZE]
        if p == 0:
            out, b = "news/index.html", "../"
        else:
            out, b = f"news/page{p + 1}/index.html", "../../"
        add(out, "Новости" if p == 0 else f"Новости — стр. {p + 1}", "news/",
            page_news_list(b, chunk, p + 1, total))
    # Новости: детали
    for it in items:
        out = f'{it["route"]}/index.html'
        det = NEWS["details"].get(it["slug"], {})
        desc = excerpt(det.get("body_html", ""), 160)
        og_img = (det["gallery"][0]["thumb"] if det.get("gallery")
                  else it["thumb"]) if it.get("thumb") else ""
        body = page_news_detail("../../", it)
        add(out, it["title"], it["route"] + "/", body, desc,
            {"title": it["title"], "description": desc,
             "image": SITE_URL.rstrip("/") + "/" + og_img if og_img else "",
             "type": "article"})
    # Контакты / Privacy
    add("kontakty/index.html", "Контакты", "kontakty/", page_contacts("../"))
    add("privacy/index.html", "Согласие на обработку персональных данных", "privacy/",
        page_privacy("../"))
    # 404
    add("404.html", "Страница не найдена", "", page_404(""))

    written = []
    for out, title, active, body, meta_desc, og in pages:
        depth = out.count("/")
        base = "../" * depth
        written.append(write(out, layout(title, base, body, active, meta_desc, og)))

    # sitemap / robots
    write("sitemap.xml", build_sitemap(sorted(routes)))
    write("robots.txt", build_robots())

    print(f"Сгенерировано страниц: {len(written)}")
    print(f"  новостей: {len(items)} (страниц списка: {total})")
    print(f"  направлений: {len(DIRECTIONS['items'])}, тренеров: {len(TRAINERS['items'])}, "
          f"достижений: {len(ACHIEVEMENTS['items'])}")
    print(f"  фото: {len(PHOTOS)}, видео: {len(VIDEOS)}")
    print("sitemap.xml и robots.txt созданы.")
    print(f"\nSITE_URL для sitemap = {SITE_URL}  (замените в build.py при публикации)")
    print("Просмотр:  python3 -m http.server 8000  ->  http://localhost:8000/")

    print(f"Сгенерировано страниц: {len(written)}")
    print(f"  новостей: {len(items)} (страниц списка: {total})")
    print(f"  направлений: {len(DIRECTIONS['items'])}, тренеров: {len(TRAINERS['items'])}, "
          f"достижений: {len(ACHIEVEMENTS['items'])}")
    print(f"  фото: {len(PHOTOS)}, видео: {len(VIDEOS)}")
    print("sitemap.xml и robots.txt созданы.")
    print(f"\nSITE_URL для sitemap = {SITE_URL}  (замените в build.py при публикации)")
    print("Просмотр:  python3 -m http.server 8000  ->  http://localhost:8000/")


if __name__ == "__main__":
    build()
