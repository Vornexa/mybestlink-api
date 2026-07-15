(() => {
  const storageKey = "mybestlink-theme";
  const systemTheme = () => window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  const requestedTheme = new URLSearchParams(window.location.search).get("theme");

  function storedTheme() {
    try {
      return localStorage.getItem(storageKey);
    } catch {
      return null;
    }
  }

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute(
      "content",
      theme === "dark" ? "#0f100e" : "#f4f4ef",
    );
  }

  applyTheme(["light", "dark"].includes(requestedTheme) ? requestedTheme : storedTheme() || systemTheme());

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        applyTheme(theme);
        try {
          localStorage.setItem(storageKey, theme);
        } catch {
          // The selected theme still applies when storage is unavailable.
        }
      });
    });
  });

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener?.("change", () => {
    if (!storedTheme()) applyTheme(systemTheme());
  });
})();
