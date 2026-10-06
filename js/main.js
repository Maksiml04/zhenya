/* =============================================================================
   Логика сайта: меню, дропдауны, модальные окна, формы, лайтбокс, анимации
   ========================================================================== */
(function () {
  "use strict";

  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ---------- Мобильное меню ---------- */
  var burger = $(".burger");
  var nav = $(".nav");
  var backdrop = $(".nav-backdrop");

  function closeNav() {
    if (!nav) return;
    nav.classList.remove("is-open");
    if (burger) burger.classList.remove("is-open");
    if (backdrop) backdrop.classList.remove("is-open");
    document.body.style.overflow = "";
  }
  function openNav() {
    if (!nav) return;
    nav.classList.add("is-open");
    if (burger) burger.classList.add("is-open");
    if (backdrop) backdrop.classList.add("is-open");
    document.body.style.overflow = "hidden";
  }
  if (burger) {
    burger.addEventListener("click", function () {
      if (nav && nav.classList.contains("is-open")) closeNav(); else openNav();
    });
  }
  if (backdrop) backdrop.addEventListener("click", closeNav);

  /* ---------- Дропдауны (клик на мобильных, hover на десктопе) ---------- */
  $$(".nav__item.has-children > .nav__link").forEach(function (link) {
    link.addEventListener("click", function (e) {
      var item = link.parentElement;
      var hasHref = link.getAttribute("href") && link.getAttribute("href") !== "#";
      // На узких экранах первый тап раскрывает подменю
      if (window.matchMedia("(max-width: 860px)").matches) {
        e.preventDefault();
        var opened = item.classList.contains("is-open");
        $$(".nav__item.is-open").forEach(function (o) { o.classList.remove("is-open"); });
        if (!opened) item.classList.add("is-open");
      } else if (!hasHref) {
        e.preventDefault();
      }
    });
  });

  document.addEventListener("click", function (e) {
    if (window.matchMedia("(max-width: 860px)").matches) return;
    if (!e.target.closest(".nav__item")) {
      $$(".nav__item.is-open").forEach(function (o) { o.classList.remove("is-open"); });
    }
  });

  /* ---------- Тень шапки при скролле ---------- */
  var header = $(".header");
  var toTop = $(".to-top");
  function onScroll() {
    var y = window.scrollY || document.documentElement.scrollTop;
    if (header) header.classList.toggle("is-scrolled", y > 8);
    if (toTop) toTop.classList.toggle("is-shown", y > 500);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  if (toTop) {
    toTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /* ---------- Модальные окна ---------- */
  function openModal(id) {
    var m = document.getElementById(id);
    if (!m) return;
    m.classList.add("is-open");
    document.body.style.overflow = "hidden";
    var first = m.querySelector("input, select, textarea");
    if (first) setTimeout(function () { first.focus(); }, 120);
  }
  function closeModal(m) {
    m.classList.remove("is-open");
    document.body.style.overflow = "";
  }
  $$("[data-modal-open]").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      openModal(btn.getAttribute("data-modal-open"));
    });
  });
  $$(".modal").forEach(function (m) {
    m.addEventListener("click", function (e) {
      if (e.target.classList.contains("modal__overlay") || e.target.closest(".modal__close")) {
        closeModal(m);
      }
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      $$(".modal.is-open").forEach(closeModal);
      closeNav();
      closeLightbox();
    }
  });

  /* ---------- Валидация + «отправка» форм ---------- */
  function validate(form) {
    var ok = true;
    $$("[required]", form).forEach(function (el) {
      var val = (el.value || "").trim();
      var bad = false;
      if (!val) bad = true;
      if (el.type === "tel" && val) bad = val.replace(/\D/g, "").length < 10;
      if (el.type === "email" && val) bad = !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
      el.classList.toggle("err", bad);
      if (bad) ok = false;
    });
    // Капча «я не робот»
    var robot = form.querySelector('input[name="robot"]');
    if (robot && !robot.checked) {
      ok = false;
      var cap = robot.closest(".captcha");
      if (cap) { cap.style.borderColor = "#d9534f"; setTimeout(function () { cap.style.borderColor = ""; }, 1600); }
    }
    // Согласие на обработку данных
    var agree = form.querySelector('input[name="agree"]');
    if (agree && !agree.checked) { ok = false; agree.classList.add("err"); } else if (agree) { agree.classList.remove("err"); }
    return ok;
  }

  function showSuccess(form) {
    var box = form.closest(".form-wrap") || form.parentElement;
    var success = box ? box.querySelector(".form-success") : null;
    if (success) {
      form.style.display = "none";
      success.classList.add("is-shown");
    } else {
      alert("Спасибо! Заявка отправлена. Мы свяжемся с вами в ближайшее время.");
    }
  }

  $$("form[data-form]").forEach(function (form) {
    // Сброс подсветки ошибок при вводе
    $$("input, select, textarea", form).forEach(function (el) {
      el.addEventListener("input", function () { el.classList.remove("err"); });
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!validate(form)) return;
      var btn = form.querySelector('button[type="submit"]');
      if (btn) { btn.disabled = true; btn.textContent = "Отправка…"; }
      // Здесь должна быть реальная отправка на сервер (fetch). Плейсхолдер:
      setTimeout(function () {
        if (btn) { btn.disabled = false; }
        showSuccess(form);
        // закрыть модалку через паузу, если форма внутри неё
        var modal = form.closest(".modal");
        if (modal) setTimeout(function () { closeModal(modal); form.reset(); resetFormState(form); }, 2200);
      }, 700);
    });
  });

  function resetFormState(form) {
    form.style.display = "";
    $$("[required]", form).forEach(function (el) { el.classList.remove("err"); });
    var box = form.closest(".form-wrap");
    var success = box ? box.querySelector(".form-success") : null;
    if (success) success.classList.remove("is-shown");
  }

  /* ---------- Маска телефона (простая) ---------- */
  $$('input[type="tel"]').forEach(function (input) {
    input.addEventListener("input", function () {
      var d = input.value.replace(/\D/g, "");
      if (d.startsWith("8")) d = "7" + d.slice(1);
      if (d.startsWith("7")) d = d.slice(1);
      d = d.slice(0, 10);
      var out = "+7";
      if (d.length > 0) out += " (" + d.slice(0, 3);
      if (d.length >= 3) out += ") " + d.slice(3, 6);
      if (d.length >= 6) out += "-" + d.slice(6, 8);
      if (d.length >= 8) out += "-" + d.slice(8, 10);
      input.value = out;
    });
  });

  /* ---------- Лайтбокс галереи ---------- */
  var lightbox = $(".lightbox");
  var lbImg = lightbox ? lightbox.querySelector("img") : null;
  var lbCap = lightbox ? lightbox.querySelector(".lightbox__cap") : null;
  function openLightbox(src, cap) {
    if (!lightbox) return;
    if (lbImg) lbImg.src = src;
    if (lbCap) lbCap.textContent = cap || "";
    lightbox.classList.add("is-open");
    document.body.style.overflow = "hidden";
  }
  function closeLightbox() {
    if (!lightbox) return;
    lightbox.classList.remove("is-open");
    document.body.style.overflow = "";
  }
  // Универсальный зум: любой элемент с data-full (или .gallery__item)
  $$(".zoomable, .gallery__item, .lead-img").forEach(function (item) {
    item.addEventListener("click", function () {
      var img = item.querySelector("img");
      var full = item.getAttribute("data-full") || (img ? img.src : "");
      if (full) openLightbox(full, item.getAttribute("data-caption") || "");
    });
  });
  if (lightbox) {
    lightbox.addEventListener("click", function (e) {
      if (e.target === lightbox || e.target.closest(".lightbox__close")) closeLightbox();
    });
  }

  /* ---------- Появление при скролле ---------- */
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("is-visible"); io.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
    $$(".reveal").forEach(function (el) { io.observe(el); });
  } else {
    $$(".reveal").forEach(function (el) { el.classList.add("is-visible"); });
  }

  /* ---------- Текущий год в подвале ---------- */
  var year = $("#year");
  if (year) year.textContent = new Date().getFullYear();
})();
