/* Pacioli News: tema claro/escuro, lista de posts (home) e página do dia (post). */
(function () {
  "use strict";

  var PER_PAGE = 10;
  var MONTHS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
                "agosto", "setembro", "outubro", "novembro", "dezembro"];

  // ---------- Tema ----------

  var root = document.documentElement;

  function storedTheme() {
    try { return localStorage.getItem("tema"); } catch (e) { return null; }
  }

  function currentTheme() {
    var t = root.getAttribute("data-theme");
    if (t) return t;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function setupThemeToggle() {
    var btn = document.querySelector(".theme-toggle");
    if (!btn) return;
    function label() {
      btn.setAttribute("aria-label", currentTheme() === "dark" ? "Usar modo claro" : "Usar modo escuro");
      btn.title = btn.getAttribute("aria-label");
    }
    label();
    btn.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("tema", next); } catch (e) { /* sem armazenamento: vale só nesta visita */ }
      label();
    });
  }

  // ---------- Utilidades ----------

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function longDate(post) {
    var p = post.date.split("-");
    return post.weekday + ", " + Number(p[2]) + " de " + MONTHS[Number(p[1]) - 1] + " de " + p[0];
  }

  function countLabel(n) {
    return n + (n === 1 ? " vídeo" : " vídeos");
  }

  function postUrl(date, anchor) {
    return "post.html?dia=" + encodeURIComponent(date) + (anchor ? "#v-" + anchor : "");
  }

  function loadIndex() {
    return fetch("posts/index.json", { cache: "no-cache" }).then(function (r) {
      if (!r.ok) throw new Error("índice indisponível");
      return r.json();
    });
  }

  function showStatus(el, msg) {
    el.innerHTML = '<p class="status">' + esc(msg) + "</p>";
  }

  // ---------- Home ----------

  function renderHome() {
    var el = document.getElementById("posts");
    var params = new URLSearchParams(location.search);
    var page = Math.max(1, parseInt(params.get("pagina"), 10) || 1);

    loadIndex().then(function (posts) {
      if (!posts.length) return showStatus(el, "Ainda não há posts publicados.");
      var pages = Math.ceil(posts.length / PER_PAGE);
      page = Math.min(page, pages);
      var slice = posts.slice((page - 1) * PER_PAGE, page * PER_PAGE);

      var html = '<ol class="post-list">' + slice.map(function (post) {
        var titles = post.videos.map(function (v) {
          return '<li><a href="' + postUrl(post.date, v.id) + '"><span class="time">' + esc(v.time) +
                 "</span>" + esc(v.title) + "</a></li>";
        }).join("");
        return '<li class="post-item">' +
          '<div class="kicker">' + esc(longDate(post)) + " · " + countLabel(post.count) + "</div>" +
          '<h2><a href="' + postUrl(post.date) + '">' + esc(post.title) + "</a></h2>" +
          (post.excerpt ? '<p class="excerpt">' + esc(post.excerpt) + "</p>" : "") +
          '<ul class="video-titles">' + titles + "</ul>" +
          "</li>";
      }).join("") + "</ol>";

      if (pages > 1) {
        html += '<nav class="pagination" aria-label="Paginação">' +
          (page > 1 ? '<a href="?pagina=' + (page - 1) + '">← Mais recentes</a>' : "<span></span>") +
          "<span>Página " + page + " de " + pages + "</span>" +
          (page < pages ? '<a href="?pagina=' + (page + 1) + '">Mais antigos →</a>' : "<span></span>") +
          "</nav>";
      }
      el.innerHTML = html;
    }).catch(function () {
      showStatus(el, "Não foi possível carregar os posts. Tente recarregar a página.");
    });
  }

  // ---------- Post ----------

  function renderPost() {
    var el = document.getElementById("post");
    var day = new URLSearchParams(location.search).get("dia") || "";
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return showStatus(el, "Post não encontrado.");

    Promise.all([
      loadIndex(),
      fetch("posts/" + day + ".md", { cache: "no-cache" }).then(function (r) {
        if (!r.ok) throw new Error("post indisponível");
        return r.text();
      })
    ]).then(function (res) {
      var posts = res[0], md = res[1];
      var i = posts.findIndex(function (p) { return p.date === day; });
      if (i < 0) return showStatus(el, "Post não encontrado.");
      var post = posts[i], newer = posts[i - 1], older = posts[i + 1];

      document.title = post.title + " · Pacioli News";

      var toc = "";
      if (post.videos.length > 1) {
        toc = '<nav class="toc" aria-label="Vídeos do dia"><p class="toc-title">Neste post</p><ul class="video-titles">' +
          post.videos.map(function (v) {
            return '<li><a href="#v-' + esc(v.id) + '"><span class="time">' + esc(v.time) + "</span>" + esc(v.title) + "</a></li>";
          }).join("") + "</ul></nav>";
      }

      var body = DOMPurify.sanitize(marked.parse(md), { ADD_ATTR: ["target"] });

      var nav = !(older || newer) ? "" : '<nav class="post-nav" aria-label="Outros dias">' +
        (older ? '<a class="prev" href="' + postUrl(older.date) + '"><small>← Post anterior</small>' + esc(older.title) + "</a>" : "") +
        (newer ? '<a class="next" href="' + postUrl(newer.date) + '"><small>Próximo post →</small>' + esc(newer.title) + "</a>" : "") +
        "</nav>";

      el.innerHTML =
        '<header class="post-header">' +
          '<div class="kicker">' + esc(longDate(post)) + "</div>" +
          "<h1>" + esc(post.title) + "</h1>" +
          '<div class="post-meta">' + countLabel(post.count) + " do canal Contabilidade Facilitada, resumidos</div>" +
        "</header>" + toc +
        '<div class="post-body">' + body + "</div>" + nav;

      if (location.hash) {
        var target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
        if (target) target.scrollIntoView();
      }
    }).catch(function () {
      showStatus(el, "Não foi possível carregar este post. Tente recarregar a página.");
    });
  }

  // ---------- Início ----------

  setupThemeToggle();
  var page = document.body.getAttribute("data-page");
  if (page === "home") renderHome();
  if (page === "post") renderPost();
})();
