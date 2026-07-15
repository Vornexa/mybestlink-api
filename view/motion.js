(() => {
  const anime = window.anime;
  const reducedMotion =
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
  const canAnimate = Boolean(anime) && !reducedMotion;
  const running = new WeakMap();

  function asArray(targets) {
    if (!targets) return [];
    if (typeof targets === "string") return [...document.querySelectorAll(targets)];
    if (targets instanceof Element) return [targets];
    return [...targets].filter(Boolean);
  }

  function cancel(target) {
    if (!target) return;
    const instance = running.get(target);
    if (instance) instance.pause();
    running.delete(target);
    if (anime) anime.remove(target);
  }

  function animate(targets, params) {
    const elements = asArray(targets);
    if (!elements.length || !canAnimate) return null;
    anime.remove(elements);
    return anime({ targets: elements, ...params });
  }

  function reveal(element) {
    element.classList.remove("reveal-ready", "is-visible");
    element.style.removeProperty("transition-delay");
    element.style.removeProperty("--reveal-delay");

    if (!canAnimate) {
      element.style.opacity = "";
      element.style.transform = "";
      return;
    }

    const delay = Math.min(Number(element.dataset.revealDelay) || 0, 180);
    animate(element, {
      opacity: [0, 1],
      translateY: [14, 0],
      duration: 560,
      delay,
      easing: "easeOutCubic",
      complete: () => {
        element.style.opacity = "";
        element.style.transform = "";
      },
    });
  }

  function initReveal() {
    const elements = [...document.querySelectorAll("[data-reveal]")];
    if (!elements.length) return;
    if (!canAnimate || !("IntersectionObserver" in window)) {
      elements.forEach(reveal);
      return;
    }

    elements.forEach((element) => {
      element.style.opacity = "0";
      element.style.transform = "translate3d(0, 14px, 0)";
    });

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          reveal(entry.target);
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -7% 0px" },
    );

    elements.forEach((element) => observer.observe(element));
  }

  function initPageIntro() {
    animate(".brand, .topbar, .hero, .console-hero", {
      opacity: [0, 1],
      translateY: [10, 0],
      duration: 520,
      delay: anime.stagger(55),
      easing: "easeOutCubic",
      complete: (instance) => instance.animatables.forEach(({ target }) => {
        target.style.opacity = "";
        target.style.transform = "";
      }),
    });

    animate(".nav-link", {
      opacity: [0, 1],
      translateX: [-8, 0],
      duration: 360,
      delay: anime.stagger(42, { start: 80 }),
      easing: "easeOutCubic",
      complete: (instance) => instance.animatables.forEach(({ target }) => {
        target.style.opacity = "";
        target.style.transform = "";
      }),
    });
  }

  function initPulseDots() {
    animate(".status-pill .pulse-dot, .runtime-chip .pulse-dot", {
      scale: [1, 1.45],
      opacity: [1, 0.58],
      duration: 1150,
      direction: "alternate",
      loop: true,
      easing: "easeInOutSine",
    });
  }

  function initHeroOrbit() {
    if (window.matchMedia?.("(max-width: 760px)").matches) return;
    animate(".orbit-ring", {
      opacity: [0.58, 1],
      duration: 2400,
      delay: anime.stagger(260),
      direction: "alternate",
      loop: true,
      easing: "easeInOutSine",
    });
    animate(".orbit-node", {
      translateY: [-4, 4],
      opacity: [0.62, 1],
      duration: 1700,
      delay: anime.stagger(280),
      direction: "alternate",
      loop: true,
      easing: "easeInOutSine",
    });
    animate(".orbit-core", {
      boxShadow: [
        "0 0 38px rgba(113,112,255,.20), inset 0 0 0 1px rgba(255,255,255,.16)",
        "0 0 70px rgba(113,112,255,.34), inset 0 0 0 1px rgba(255,255,255,.24)",
      ],
      duration: 2200,
      direction: "alternate",
      loop: true,
      easing: "easeInOutSine",
    });
  }

  function animateSoftLoading(container) {
    if (!container || !canAnimate) return null;
    const targets = [...container.querySelectorAll("span, div")];
    if (!targets.length) return null;
    const instance = animate(targets, {
      backgroundColor: ["rgba(255,255,255,.045)", "rgba(255,255,255,.095)"],
      duration: 850,
      delay: anime.stagger(70),
      direction: "alternate",
      loop: true,
      easing: "easeInOutSine",
    });
    if (instance) running.set(container, instance);
    return instance;
  }

  function animateItems(items, options = {}) {
    const elements = asArray(items);
    if (!elements.length || !canAnimate) return;
    animate(elements, {
      opacity: [0, 1],
      translateY: [options.y ?? 10, 0],
      duration: options.duration ?? 360,
      delay: anime.stagger(options.stagger ?? 45),
      easing: "easeOutCubic",
      complete: () => elements.forEach((item) => {
        item.style.opacity = "";
        item.style.transform = "";
      }),
    });
  }

  function animateCards(container = document) {
    animateItems(container.querySelectorAll(
      ".stat-card, .connector-card:not(.connector-skeleton), .endpoint-row, .console-card, .result-card",
    ), { y: 12, stagger: 38, duration: 380 });
  }

  function startGather(button) {
    const icon = button?.querySelector(".gather-icon");
    if (!icon || !canAnimate) return null;
    cancel(icon);
    const instance = animate(icon, {
      translateY: [0, 4],
      duration: 420,
      direction: "alternate",
      loop: true,
      easing: "easeInOutSine",
    });
    if (instance) running.set(icon, instance);
    return instance;
  }

  function stopGather(button) {
    const icon = button?.querySelector(".gather-icon");
    if (!icon) return;
    cancel(icon);
    icon.style.transform = "";
  }

  function setProgress(element, percent) {
    if (!element) return;
    if (!canAnimate) {
      element.style.width = `${percent}%`;
      return;
    }
    animate(element, {
      width: `${percent}%`,
      duration: 360,
      easing: "easeOutCubic",
    });
  }

  function ensureNavIndicator(nav) {
    let indicator = nav.querySelector(".nav-indicator");
    if (!indicator) {
      indicator = document.createElement("span");
      indicator.className = "nav-indicator";
      indicator.setAttribute("aria-hidden", "true");
      nav.prepend(indicator);
    }
    return indicator;
  }

  function moveNavIndicator(link) {
    if (!link) return;
    const nav = link.closest(".nav");
    if (!nav) return;
    const indicator = ensureNavIndicator(nav);
    const x = link.offsetLeft;
    const y = link.offsetTop;
    const width = link.offsetWidth;
    const height = link.offsetHeight;
    if (!canAnimate) {
      indicator.style.opacity = "1";
      indicator.style.width = `${width}px`;
      indicator.style.height = `${height}px`;
      indicator.style.transform = `translate3d(${x}px, ${y}px, 0)`;
      return;
    }
    animate(indicator, {
      opacity: [Number(getComputedStyle(indicator).opacity) || 0, 1],
      width,
      height,
      translateX: x,
      translateY: y,
      duration: 260,
      easing: "easeOutCubic",
    });
  }

  function ensureActiveNavVisible(link) {
    if (!link || !window.matchMedia?.("(max-width: 760px)").matches) return;
    link.scrollIntoView({ block: "nearest", inline: "center", behavior: "smooth" });
  }

  function flash(targets) {
    animate(targets, {
      scale: [1, 1.015, 1],
      duration: 360,
      easing: "easeOutCubic",
    });
  }

  window.MyBestMotion = {
    enabled: canAnimate,
    reveal,
    animateItems,
    animateCards,
    animateSoftLoading,
    startGather,
    stopGather,
    setProgress,
    moveNavIndicator,
    flash,
    cancel,
  };

  initReveal();
  initPageIntro();
  initPulseDots();
  initHeroOrbit();
  document.querySelectorAll(".connector-skeleton, .loading-lines").forEach(animateSoftLoading);
  requestAnimationFrame(() => {
    const active = document.querySelector(".nav-link.is-active");
    if (active) {
      ensureActiveNavVisible(active);
      moveNavIndicator(active);
      window.setTimeout(() => moveNavIndicator(active), 360);
    }
  });
  window.addEventListener("resize", () => {
    const active = document.querySelector(".nav-link.is-active");
    if (active) moveNavIndicator(active);
  });
})();
