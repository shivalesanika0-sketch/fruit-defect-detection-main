/* ===== Produce AI 2026 — Shared Site JS ===== */

(function () {
  /* -- Theme: zero-lag no-trans trick -- */
  var noTransStyle = document.createElement("style");
  noTransStyle.textContent = "html.no-trans,html.no-trans *{transition:none!important;}";
  document.head.appendChild(noTransStyle);

  var html = document.documentElement;

  function applyTheme(dark) {
    html.classList.add("no-trans");
    if (dark) { html.classList.add("dark"); localStorage.setItem("theme","dark"); }
    else       { html.classList.remove("dark"); localStorage.setItem("theme","light"); }
    requestAnimationFrame(function(){ requestAnimationFrame(function(){ html.classList.remove("no-trans"); }); });
  }

  // Restore on load
  try { if (localStorage.getItem("theme") === "dark") html.classList.add("dark"); } catch(_){}

  document.addEventListener("DOMContentLoaded", function () {

    /* Theme toggles (multiple possible) */
    document.querySelectorAll(".theme-btn").forEach(function(btn){
      btn.addEventListener("click", function(){
        applyTheme(!html.classList.contains("dark"));
      });
    });

    /* Mobile nav hamburger */
    var hamburger = document.querySelector(".nav-hamburger");
    var navLinks  = document.querySelector(".nav-links");
    if (hamburger && navLinks) {
      hamburger.addEventListener("click", function(){
        navLinks.classList.toggle("open");
      });
    }

    /* Active nav link */
    var current = window.location.pathname;
    document.querySelectorAll(".nav-link").forEach(function(link){
      if (link.getAttribute("href") === current) link.classList.add("active");
    });

    /* Accordion */
    document.querySelectorAll(".accordion-trigger").forEach(function(trigger){
      trigger.addEventListener("click", function(){
        var item = trigger.closest(".accordion-item");
        item.classList.toggle("open");
      });
    });

    /* Animate bars on page load */
    document.querySelectorAll("[data-fill]").forEach(function(el){
      setTimeout(function(){ el.style.width = el.getAttribute("data-fill"); }, 300);
    });

    /* Scroll reveal — add .reveal class to any element */
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function(entries){
        entries.forEach(function(e){
          if (e.isIntersecting) { e.target.classList.add("revealed"); io.unobserve(e.target); }
        });
      }, { threshold: 0.12 });
      document.querySelectorAll(".reveal").forEach(function(el){ io.observe(el); });
    } else {
      document.querySelectorAll(".reveal").forEach(function(el){ el.classList.add("revealed"); });
    }

  });
})();
