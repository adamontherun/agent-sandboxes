/* Course book behavior: theme, mobile nav, highlighting, copy buttons — reusable across topics */
(function () {
  "use strict";

  // ---- theme ----------------------------------------------------------
  const root = document.documentElement;

  function applyTheme(theme) {
    root.dataset.theme = theme;
    const btn = document.querySelector(".theme-toggle");
    if (btn) btn.textContent = theme === "dark" ? "☀ Light mode" : "☾ Dark mode";
  }

  const stored = localStorage.getItem("book-theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)");
  applyTheme(stored || (prefersDark.matches ? "dark" : "light"));

  prefersDark.addEventListener("change", (e) => {
    if (!localStorage.getItem("book-theme")) {
      applyTheme(e.matches ? "dark" : "light");
    }
  });

  document.addEventListener("click", (e) => {
    if (e.target.closest(".theme-toggle")) {
      const next = root.dataset.theme === "dark" ? "light" : "dark";
      localStorage.setItem("book-theme", next);
      applyTheme(next);
    }
  });

  // ---- mobile sidebar --------------------------------------------------
  document.addEventListener("click", (e) => {
    const sidebar = document.querySelector(".sidebar");
    if (!sidebar) return;
    if (e.target.closest(".menu-btn")) {
      sidebar.classList.toggle("open");
    } else if (sidebar.classList.contains("open") && !e.target.closest(".sidebar")) {
      sidebar.classList.remove("open");
    }
  });

  // ---- syntax highlighting + copy buttons ------------------------------
  window.addEventListener("DOMContentLoaded", () => {
    if (window.hljs) {
      document.querySelectorAll("pre code").forEach((el) => {
        window.hljs.highlightElement(el);
      });
    }

    document.querySelectorAll(".codeblock").forEach((block) => {
      const label = block.querySelector(".code-label");
      const code = block.querySelector("pre code");
      if (!label || !code) return;
      const btn = document.createElement("button");
      btn.className = "copy-btn";
      btn.type = "button";
      btn.textContent = "copy";
      btn.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(code.textContent);
          btn.textContent = "copied!";
        } catch {
          btn.textContent = "press ⌘C";
        }
        setTimeout(() => (btn.textContent = "copy"), 1600);
      });
      label.appendChild(btn);
    });
  });
})();
