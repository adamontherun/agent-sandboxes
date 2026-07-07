/* Course book behavior: theme, mobile nav, highlighting, copy buttons — reusable across topics */
(function () {
  "use strict";

  // ---- analytics (PostHog) --------------------------------------------
  // PH_KEY is a *public* PostHog project token — it is designed to be embedded
  // in client-side pages. Never put a personal API key (phx_...) here.
  var PH_KEY = "phc_cXvb2Otk0GPp9scI79MUbhtT39gaeaBQu6muFZOVmoJ";
  var PH_HOST = "https://us.i.posthog.com";
  var COURSE = "agent-sandboxes";

  function pageContext() {
    var kicker = document.querySelector(".kicker");
    if (!kicker) return { page_type: "home" };
    var ctx = { page_type: "chapter" };
    var cm = kicker.textContent.match(/Chapter\s+(\d+)/i);
    if (cm) ctx.chapter_number = Number(cm[1]);
    var pm = kicker.textContent.match(/Part\s+([^·—-]+)/i);
    if (pm) ctx.part = pm[1].trim();
    var h1 = document.querySelector("main article h1");
    if (h1) ctx.chapter_title = h1.textContent.trim();
    return ctx;
  }

  function wireAnalyticsEvents() {
    // Codespace launch — the headline signal — plus GitHub repo clicks.
    document.addEventListener("click", function (e) {
      var cs = e.target.closest('a.codespace-link, a[href*="codespaces.new"]');
      if (cs) {
        var loc = cs.closest(".sidebar") ? "sidebar"
          : cs.closest(".tryit") ? "tryit" : "hero";
        window.posthog.capture("codespace_launch_clicked", { location: loc, href: cs.href });
        return;
      }
      var repo = e.target.closest("a.repo-link");
      if (repo) window.posthog.capture("repo_link_clicked", { href: repo.href });
    });

    // Scroll depth — how far into a chapter readers get.
    var marks = [25, 50, 75, 100], seen = {};
    window.addEventListener("scroll", function () {
      var d = document.documentElement;
      var scrollable = d.scrollHeight - d.clientHeight;
      if (scrollable <= 0) return;
      var pct = (d.scrollTop / scrollable) * 100;
      for (var i = 0; i < marks.length; i++) {
        if (pct >= marks[i] && !seen[marks[i]]) {
          seen[marks[i]] = true;
          window.posthog.capture("scroll_depth", { depth: marks[i] });
        }
      }
    }, { passive: true });

    // Section visibility — which passages readers actually reach.
    if ("IntersectionObserver" in window) {
      var headings = document.querySelectorAll("main article h2, .tryit h3");
      var fired = {};
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          var idx = en.target.dataset.sectionIndex;
          if (fired[idx]) return;
          fired[idx] = true;
          window.posthog.capture("section_viewed", {
            section: en.target.textContent.trim(),
            section_index: Number(idx)
          });
        });
      }, { threshold: 0.5 });
      headings.forEach(function (h, i) {
        h.dataset.sectionIndex = i;
        io.observe(h);
      });
    }
  }

  if (PH_KEY && PH_KEY.indexOf("{{") !== 0) {
    // PostHog array-stub loader (official snippet).
    !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug getPageViewId captureTraceFeedback captureTraceMetric".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
    window.posthog.init(PH_KEY, {
      api_host: PH_HOST,
      defaults: "2026-05-30",
      person_profiles: "identified_only",
      capture_pageview: false
    });
    var ctx = pageContext();
    var superProps = { course: COURSE };
    for (var k in ctx) superProps[k] = ctx[k];
    window.posthog.register(superProps);
    // Clear stale chapter props (persisted from a prior page) on non-chapter pages.
    ["chapter_number", "chapter_title", "part"].forEach(function (key) {
      if (!(key in ctx)) window.posthog.unregister(key);
    });
    window.posthog.capture("$pageview");
    wireAnalyticsEvents();
  }

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
      if (window.posthog) window.posthog.capture("theme_changed", { theme: next });
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
        if (window.posthog) window.posthog.capture("code_copied", { label: label.firstChild ? label.firstChild.textContent.trim() : "" });
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
