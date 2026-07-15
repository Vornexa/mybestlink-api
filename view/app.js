const state = {
  config: null,
  connectors: [],
  dirty: false,
};

const $ = (selector) => document.querySelector(selector);
const connectorGrid = $("#connector-grid");
const configForm = $("#config-form");
const toast = $("#toast");
let toastTimer;

function showToast(message, isError = false) {
  clearTimeout(toastTimer);
  toast.textContent = message;
  toast.classList.toggle("is-error", isError);
  toast.classList.add("is-visible");
  toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 3200);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: options.body ? { "Content-Type": "application/json" } : {},
    ...options,
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.message || `Request failed (${response.status})`);
  return body;
}

function renderSummary(data) {
  $("#api-status").textContent = "API operational";
  $("#stat-status").textContent = "Online";
  $("#stat-host").textContent = `${data.runtime.host}:${data.runtime.port}`;
  $("#stat-connectors").textContent = data.connectors.length;
  $("#stat-endpoints").textContent = data.runtime.endpoint_count;
  $("#stat-cookies").textContent = data.runtime.cookie_count;
  $("#connector-count").textContent = `${data.connectors.length} connectors`;
  window.MyBestMotion?.flash(document.querySelectorAll(".stat-card"));
}

function connectorCard(connector) {
  const article = document.createElement("article");
  article.className = "connector-card";
  article.dataset.connector = connector.id;

  const head = document.createElement("div");
  head.className = "connector-head";
  const title = document.createElement("div");
  title.className = "connector-title";
  const logo = document.createElement("span");
  logo.className = "connector-logo";
  logo.textContent = connector.id === "elearning" ? "EL" : "EX";
  const copy = document.createElement("div");
  const heading = document.createElement("h3");
  heading.textContent = connector.name;
  const purpose = document.createElement("p");
  purpose.textContent = connector.purpose;
  copy.append(heading, purpose);
  title.append(logo, copy);
  const status = document.createElement("span");
  status.className = "connector-status";
  status.textContent = "Not checked";
  head.append(title, status);

  const label = document.createElement("label");
  label.className = "field-label";
  label.htmlFor = `url-${connector.id}`;
  label.textContent = "Base URL";
  const input = document.createElement("input");
  input.className = "url-field";
  input.id = `url-${connector.id}`;
  input.type = "url";
  input.required = true;
  input.value = connector.base_url;
  input.autocomplete = "off";
  input.spellcheck = false;
  input.addEventListener("input", markDirty);

  const actions = document.createElement("div");
  actions.className = "connector-actions";
  const latency = document.createElement("span");
  latency.className = "latency";
  latency.textContent = "Awaiting test";
  const button = document.createElement("button");
  button.className = "button button-secondary button-small";
  button.type = "button";
  button.textContent = "Test connection";
  button.addEventListener("click", () => testConnector(connector.id, input, status, latency, button));
  actions.append(latency, button);
  article.append(head, label, input, actions);
  return article;
}

function renderConnectors(connectors) {
  const cards = connectors.map(connectorCard);
  connectorGrid.replaceChildren(...cards);
  requestAnimationFrame(() => window.MyBestMotion?.animateItems(cards, { y: 12, stagger: 55 }));
}

function renderEndpoints(endpoints) {
  const rows = endpoints.map((endpoint) => {
    const row = document.createElement("div");
    row.className = "endpoint-row";
    const method = document.createElement("span");
    method.className = `method ${endpoint.method.toLowerCase()}`;
    method.textContent = endpoint.method;
    const route = document.createElement("span");
    route.className = "route";
    route.textContent = endpoint.path;
    route.title = endpoint.path;
    const description = document.createElement("span");
    description.className = "endpoint-description";
    description.textContent = endpoint.description;
    row.append(method, route, description);
    return row;
  });
  $("#endpoint-list").replaceChildren(...rows);
  requestAnimationFrame(() => window.MyBestMotion?.animateItems(rows, { y: 8, stagger: 35 }));
}

function renderConfig(config) {
  $("#request-timeout").value = config.request_timeout_seconds;
  $("#verify-ssl").checked = config.verify_ssl;
  state.config = { ...config };
  state.dirty = false;
  $("#save-note").textContent = "No unsaved changes";
}

function render(data) {
  state.connectors = data.connectors;
  renderSummary(data);
  renderConnectors(data.connectors);
  renderEndpoints(data.endpoints);
  renderConfig(data.config);
}

function markDirty() {
  state.dirty = true;
  $("#save-note").textContent = "Unsaved changes";
}

async function loadControlPanel(showSuccess = false) {
  const refreshButton = $("#refresh-button");
  refreshButton.disabled = true;
  try {
    const data = await api("/cp/api/config");
    render(data);
    if (showSuccess) showToast("Control panel refreshed");
  } catch (error) {
    $("#api-status").textContent = "API unavailable";
    $("#stat-status").textContent = "Error";
    showToast(error.message, true);
  } finally {
    refreshButton.disabled = false;
  }
}

async function testConnector(id, input, status, latency, button) {
  button.disabled = true;
  button.textContent = "Testing…";
  status.className = "connector-status";
  status.textContent = "Checking";
  latency.textContent = "Sending request";
  try {
    const result = await api("/cp/api/connectors/test", {
      method: "POST",
      body: JSON.stringify({ connector: id, url: input.value }),
    });
    status.classList.add(result.reachable ? "online" : "offline");
    status.textContent = result.reachable ? "Reachable" : "Unavailable";
    latency.textContent = result.http_status
      ? `HTTP ${result.http_status} · ${result.latency_ms} ms`
      : `${result.latency_ms} ms · no response`;
    showToast(`${id === "elearning" ? "eLearning" : "Exam"}: ${result.message}`, !result.reachable);
  } catch (error) {
    status.classList.add("offline");
    status.textContent = "Invalid config";
    latency.textContent = "Test failed";
    showToast(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = "Test connection";
  }
}

configForm.addEventListener("input", markDirty);
configForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const saveButton = $("#save-button");
  const elearning = $("#url-elearning");
  const exam = $("#url-exam");
  if (!elearning?.reportValidity() || !exam?.reportValidity() || !configForm.reportValidity()) return;

  const payload = {
    elearning_base_url: elearning.value,
    exam_base_url: exam.value,
    request_timeout_seconds: Number($("#request-timeout").value),
    verify_ssl: $("#verify-ssl").checked,
  };
  saveButton.disabled = true;
  saveButton.textContent = "Saving…";
  try {
    const data = await api("/cp/api/config", { method: "PUT", body: JSON.stringify(payload) });
    render(data);
    showToast("Configuration saved and applied");
  } catch (error) {
    showToast(error.message, true);
  } finally {
    saveButton.disabled = false;
    saveButton.textContent = "Save configuration";
  }
});

$("#refresh-button").addEventListener("click", () => loadControlPanel(true));

const sections = [...document.querySelectorAll("[data-section]")];
const navLinks = [...document.querySelectorAll("[data-nav]")];
let scrollTicking = false;

function navTargetName(link) {
  if (link.dataset.nav) return link.dataset.nav;
  const hash = new URL(link.href, location.href).hash.replace("#", "");
  return hash || "overview";
}

function ensureActiveNavVisible(link) {
  if (!link || !window.matchMedia?.("(max-width: 760px)").matches) return;
  link.scrollIntoView({ block: "nearest", inline: "center", behavior: "smooth" });
}

function setActiveNav(sectionName) {
  let activeLink;
  navLinks.forEach((link) => {
    const active = navTargetName(link) === sectionName;
    link.classList.toggle("is-active", active);
    if (active) activeLink = link;
  });
  ensureActiveNavVisible(activeLink);
  window.MyBestMotion?.moveNavIndicator(activeLink);
  window.setTimeout(() => window.MyBestMotion?.moveNavIndicator(activeLink), 360);
}

function currentSectionName() {
  const probeY = window.innerHeight < 760 ? 112 : Math.round(window.innerHeight * 0.26);
  let current = sections[0]?.dataset.section || "overview";
  sections.forEach((section) => {
    if (section.getBoundingClientRect().top <= probeY) current = section.dataset.section;
  });
  return current;
}

function updateActiveFromScroll() {
  scrollTicking = false;
  if (!sections.length) return;
  setActiveNav(currentSectionName());
}

if (sections.length && navLinks.length && "IntersectionObserver" in window) {
  const sectionObserver = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (!visible) return;
    setActiveNav(visible.target.dataset.section);
  }, { rootMargin: "-15% 0px -65%", threshold: [0, .2, .6] });
  sections.forEach((section) => sectionObserver.observe(section));
}

window.addEventListener("scroll", () => {
  if (scrollTicking) return;
  scrollTicking = true;
  requestAnimationFrame(updateActiveFromScroll);
}, { passive: true });

navLinks.forEach((link) => {
  link.addEventListener("click", (event) => {
    const url = new URL(link.href, location.href);
    const samePageHash = url.pathname === location.pathname && url.hash;
    if (samePageHash) {
      event.preventDefault();
      const target = document.querySelector(url.hash);
      if (target) {
        history.pushState(null, "", url.hash);
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
    setActiveNav(navTargetName(link));
  });
});

window.addEventListener("hashchange", updateActiveFromScroll);
setActiveNav(location.hash.replace("#", "") || "overview");

window.addEventListener("beforeunload", (event) => {
  if (!state.dirty) return;
  event.preventDefault();
  event.returnValue = "";
});

loadControlPanel();
