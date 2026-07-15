(() => {
  const anime = window.anime;
  const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
  const canAnimate = Boolean(anime) && !reducedMotion;
  const running = new WeakMap();

  function asArray(targets) {
    if (!targets) return [];
    if (typeof targets === "string") return [...document.querySelectorAll(targets)];
    if (targets instanceof Element) return [targets];
    return [...targets].filter(Boolean);
  }

  function animate(targets, params) {
    const elements = asArray(targets);
    if (!elements.length || !canAnimate) return null;
    anime.remove(elements);
    return anime({ targets: elements, ...params });
  }

  function cancel(target) {
    if (!target) return;
    running.get(target)?.pause();
    running.delete(target);
    anime?.remove(target);
  }

  function reveal(element) {
    if (!canAnimate) {
      element.style.opacity = "";
      element.style.transform = "";
      return;
    }
    animate(element, {
      opacity: [0, 1],
      translateY: [18, 0],
      duration: 650,
      delay: Math.min(Number(element.dataset.revealDelay) || 0, 180),
      easing: "easeOutExpo",
      complete: () => {
        element.style.opacity = "";
        element.style.transform = "";
      },
    });
  }

  function initReveal() {
    const elements = [...document.querySelectorAll("[data-reveal]")];
    if (!canAnimate || !("IntersectionObserver" in window)) {
      elements.forEach(reveal);
      return;
    }
    elements.forEach((element) => {
      element.style.opacity = "0";
      element.style.transform = "translate3d(0,18px,0)";
    });
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        reveal(entry.target);
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.1, rootMargin: "0px 0px -6%" });
    elements.forEach((element) => observer.observe(element));
  }

  function animateItems(items, options = {}) {
    const elements = asArray(items);
    if (!elements.length || !canAnimate) return;
    animate(elements, {
      opacity: [0, 1],
      translateY: [options.y ?? 12, 0],
      duration: options.duration ?? 480,
      delay: anime.stagger(options.stagger ?? 45),
      easing: "easeOutExpo",
      complete: () => elements.forEach((element) => {
        element.style.opacity = "";
        element.style.transform = "";
      }),
    });
  }

  function animateCards(container = document) {
    animateItems(container.querySelectorAll(".stat-card,.connector-card:not(.connector-skeleton),.endpoint-row,.console-card,.result-card"));
  }

  function animateSoftLoading(container) {
    if (!container || !canAnimate) return null;
    const targets = [...container.querySelectorAll("span,div")];
    const instance = animate(targets, {
      opacity: [.38, 1],
      duration: 780,
      delay: anime.stagger(70),
      direction: "alternate",
      loop: true,
      easing: "easeInOutSine",
    });
    if (instance) running.set(container, instance);
    return instance;
  }

  function startGather(button) {
    const icon = button?.querySelector(".gather-icon");
    if (!icon || !canAnimate) return null;
    cancel(icon);
    const instance = animate(icon, {
      scale: [1, .84],
      rotate: [0, 360],
      duration: 850,
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
    animate(element, { width: `${percent}%`, duration: 420, easing: "easeOutExpo" });
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
    const values = {
      opacity: 1,
      width: link.offsetWidth,
      height: link.offsetHeight,
      translateX: link.offsetLeft,
      translateY: link.offsetTop,
    };
    if (!canAnimate) {
      Object.assign(indicator.style, {
        opacity: "1",
        width: `${values.width}px`,
        height: `${values.height}px`,
        transform: `translate3d(${values.translateX}px,${values.translateY}px,0)`,
      });
      return;
    }
    animate(indicator, { ...values, duration: 320, easing: "easeOutExpo" });
  }

  function flash(targets) {
    animate(targets, { scale: [1, 1.018, 1], duration: 440, easing: "easeOutQuad" });
  }

  function initIntro() {
    animate(".brand", {
      opacity: [0, 1],
      translateY: [-8, 0],
      duration: 560,
      delay: anime.stagger(80),
      easing: "easeOutExpo",
    });
    animate(".nav-link", {
      opacity: [0, 1],
      translateX: [-10, 0],
      duration: 480,
      delay: anime.stagger(45, { start: 120 }),
      easing: "easeOutExpo",
    });
  }

  function initTopology() {
    const paths = [...document.querySelectorAll(".topology-lines path")];
    paths.forEach((path) => {
      const length = path.getTotalLength();
      path.style.strokeDasharray = `4 5 ${length}`;
      path.style.strokeDashoffset = length;
    });
    animate(paths, {
      strokeDashoffset: 0,
      duration: 1300,
      delay: anime.stagger(120, { start: 420 }),
      easing: "easeOutCubic",
    });
    animate(".topology-node", {
      translateY: [-3, 3],
      duration: 1600,
      delay: anime.stagger(180),
      direction: "alternate",
      loop: true,
      easing: "easeInOutSine",
    });
    animate(".topology-core", {
      boxShadow: [
        "0 0 0 1px #597eff, 0 0 30px rgba(36,85,245,.22)",
        "0 0 0 1px #7998ff, 0 0 58px rgba(36,85,245,.48)",
      ],
      duration: 1500,
      direction: "alternate",
      loop: true,
      easing: "easeInOutSine",
    });
  }

  function initAmbientMotion() {
    animate(".pulse-dot", {
      scale: [1, 1.35],
      opacity: [1, .62],
      duration: 1100,
      direction: "alternate",
      loop: true,
      easing: "easeInOutSine",
    });
    animate(".request-stack span", {
      translateX: [0, 4],
      duration: 1450,
      delay: anime.stagger(180),
      direction: "alternate",
      loop: true,
      easing: "easeInOutSine",
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

  window.lucide?.createIcons({ attrs: { "aria-hidden": "true" } });
  initReveal();
  initIntro();
  initTopology();
  initAmbientMotion();
  document.querySelectorAll(".connector-skeleton,.loading-lines").forEach(animateSoftLoading);
  requestAnimationFrame(() => moveNavIndicator(document.querySelector(".nav-link.is-active")));
  window.addEventListener("resize", () => moveNavIndicator(document.querySelector(".nav-link.is-active")));
})();
