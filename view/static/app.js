const state = {
  config: null,
  connectors: [],
  dirty: false,
};

const $ = (selector) => document.querySelector(selector);
const connectorGrid = $("#connector-grid");
const configForm = $("#config-form");
const connectorForm = $("#connector-form");
const toast = $("#toast");
let toastTimer;

function setButtonLabel(button, label) {
  const labelElement = button.querySelector("[data-button-label]");
  if (labelElement) labelElement.textContent = label;
  else button.textContent = label;
}

function updateClock() {
  const clock = $("#dashboard-clock");
  if (!clock) return;
  clock.textContent = new Intl.DateTimeFormat("en", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date());
}

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
  if ($("#api-status")) $("#api-status").textContent = "API operational";
  if ($("#stat-status")) $("#stat-status").textContent = "Online";
  if ($("#stat-host")) $("#stat-host").textContent = `${data.runtime.host}:${data.runtime.port}`;
  if ($("#stat-connectors")) $("#stat-connectors").textContent = data.connectors.length;
  if ($("#stat-endpoints")) $("#stat-endpoints").textContent = data.runtime.endpoint_count;
  if ($("#stat-cookies")) $("#stat-cookies").textContent = data.runtime.cookie_count;
  if ($("#connector-count")) $("#connector-count").textContent = `${data.connectors.length} connectors`;
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
  if (!connectorGrid) return;
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
  const endpointList = $("#endpoint-list");
  if (!endpointList) return;
  endpointList.replaceChildren(...rows);
  requestAnimationFrame(() => window.MyBestMotion?.animateItems(rows, { y: 8, stagger: 35 }));
}

function renderConfig(config) {
  if ($("#request-timeout")) $("#request-timeout").value = config.request_timeout_seconds;
  if ($("#verify-ssl")) $("#verify-ssl").checked = config.verify_ssl;
  state.config = { ...config };
  state.dirty = false;
  if ($("#save-note")) $("#save-note").textContent = "No unsaved changes";
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
  if ($("#save-note")) $("#save-note").textContent = "Unsaved changes";
}

async function loadControlPanel(showSuccess = false) {
  const refreshButton = $("#refresh-button");
  refreshButton.disabled = true;
  try {
    const data = await api("/cp/api/config");
    render(data);
    if (showSuccess) showToast("Control panel refreshed");
  } catch (error) {
    if ($("#api-status")) $("#api-status").textContent = "API unavailable";
    if ($("#stat-status")) $("#stat-status").textContent = "Error";
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

async function saveConfiguration(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const saveButton = $("#save-button");
  const elearning = $("#url-elearning");
  const exam = $("#url-exam");
  if (elearning && !elearning.reportValidity()) return;
  if (exam && !exam.reportValidity()) return;
  if (!form.reportValidity() || !state.config) return;

  const payload = {
    elearning_base_url: elearning?.value ?? state.config.elearning_base_url,
    exam_base_url: exam?.value ?? state.config.exam_base_url,
    request_timeout_seconds: $("#request-timeout")
      ? Number($("#request-timeout").value)
      : state.config.request_timeout_seconds,
    verify_ssl: $("#verify-ssl")?.checked ?? state.config.verify_ssl,
  };
  saveButton.disabled = true;
  setButtonLabel(saveButton, "Applying...");
  try {
    const data = await api("/cp/api/config", { method: "PUT", body: JSON.stringify(payload) });
    render(data);
    showToast("Configuration saved and applied");
  } catch (error) {
    showToast(error.message, true);
  } finally {
    saveButton.disabled = false;
    setButtonLabel(
      saveButton,
      form === connectorForm ? "Save connectors" : "Apply configuration",
    );
  }
}

[configForm, connectorForm].filter(Boolean).forEach((form) => {
  form.addEventListener("input", markDirty);
  form.addEventListener("submit", saveConfiguration);
});

$("#refresh-button").addEventListener("click", () => loadControlPanel(true));

window.addEventListener("beforeunload", (event) => {
  if (!state.dirty) return;
  event.preventDefault();
  event.returnValue = "";
});

window.lucide?.createIcons({ attrs: { "aria-hidden": "true" } });
updateClock();
window.setInterval(updateClock, 30_000);
loadControlPanel();
