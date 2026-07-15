const $ = (selector, parent = document) => parent.querySelector(selector);
const toast = $("#toast");
const gatherButton = $("#gather-button");
const progress = $("#gather-progress");
let toastTimer;

const requests = [
  { id: "health", path: "/health" },
  { id: "dashboard", path: "/dashboard" },
  { id: "kuliah", path: "/jadwal/kuliah" },
  { id: "pengganti", path: "/jadwal/pengganti" },
  { id: "uts", path: "/jadwal/ujian?type=uts" },
  { id: "uas", path: "/jadwal/ujian?type=uas" },
];

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
  let body;
  try {
    body = await response.json();
  } catch {
    body = { message: "Response is not valid JSON" };
  }
  if (!response.ok) throw new Error(body.message || `Request failed (${response.status})`);
  return body;
}

function setStatus(element, label, kind = "") {
  element.className = `connector-status ${kind}`.trim();
  element.textContent = label;
}

function valueText(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "object") {
    return Object.entries(value).map(([key, item]) => `${key.replaceAll("_", " ")}: ${valueText(item)}`).join(" · ");
  }
  return String(value);
}

function fieldList(data) {
  const list = document.createElement("dl");
  list.className = "result-fields";
  Object.entries(data).forEach(([key, value]) => {
    const wrapper = document.createElement("div");
    const term = document.createElement("dt");
    const detail = document.createElement("dd");
    term.textContent = key.replaceAll("_", " ");
    detail.textContent = valueText(value);
    wrapper.append(term, detail);
    list.append(wrapper);
  });
  return list;
}

function scheduleList(items) {
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No schedule found.";
    return empty;
  }
  const list = document.createElement("div");
  list.className = "schedule-list";
  const cards = [];
  items.forEach((item, index) => {
    const card = document.createElement("article");
    const title = document.createElement("strong");
    title.textContent = item.matakuliah || item.mata_kuliah || item.kode_mtk || `Item ${index + 1}`;
    card.append(title, fieldList(item));
    list.append(card);
    cards.push(card);
  });
  requestAnimationFrame(() => window.MyBestMotion?.animateItems(cards));
  return list;
}

function resultCard(id) {
  return $(`[data-result="${id}"]`);
}

function markLoading(id) {
  const card = resultCard(id);
  card.classList.remove("has-error", "has-data");
  card.classList.add("is-fetching");
  $(".result-state", card).textContent = "Loading";
  const body = $(".result-body", card);
  body.className = "result-body loading-lines";
  body.replaceChildren(...Array.from({ length: 3 }, () => document.createElement("span")));
  window.MyBestMotion?.animateSoftLoading(body);
}

function renderResult(id, data) {
  const card = resultCard(id);
  const body = $(".result-body", card);
  window.MyBestMotion?.cancel(body);
  const schedules = data?.data?.jadwal;
  card.classList.remove("is-fetching", "has-error");
  card.classList.add("has-data");
  $(".result-state", card).textContent = Array.isArray(schedules) ? `${schedules.length} items` : "Ready";
  body.className = "result-body";
  body.replaceChildren(Array.isArray(schedules) ? scheduleList(schedules) : fieldList(data));
}

function renderError(id, message) {
  const card = resultCard(id);
  const body = $(".result-body", card);
  window.MyBestMotion?.cancel(body);
  card.classList.remove("is-fetching", "has-data");
  card.classList.add("has-error");
  $(".result-state", card).textContent = "Failed";
  body.className = "result-body result-error";
  body.textContent = message;
}

async function checkHealth() {
  try {
    await api("/health");
    $("#console-status").textContent = "API operational";
  } catch {
    $("#console-status").textContent = "API unavailable";
    $("#console-dot").classList.add("is-offline");
  }
}

async function gatherAll() {
  gatherButton.disabled = true;
  gatherButton.classList.add("is-gathering");
  window.MyBestMotion?.startGather(gatherButton);
  window.MyBestMotion?.setProgress(progress, 0);
  $("#gather-note").textContent = "Collecting responses…";
  requests.forEach(({ id }) => markLoading(id));
  let completed = 0;

  await Promise.all(requests.map(async ({ id, path }) => {
    try {
      renderResult(id, await api(path));
    } catch (error) {
      renderError(id, error.message);
    } finally {
      completed += 1;
      window.MyBestMotion?.setProgress(progress, (completed / requests.length) * 100);
    }
  }));

  gatherButton.disabled = false;
  gatherButton.classList.remove("is-gathering");
  window.MyBestMotion?.stopGather(gatherButton);
  $("#gather-note").textContent = `Finished ${completed} requests.`;
  $("#results").scrollIntoView({ behavior: "smooth", block: "start" });
  showToast("Data gathering complete");
}

gatherButton.addEventListener("click", gatherAll);

$("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $("#login-button");
  const status = $("#login-status");
  button.disabled = true;
  button.textContent = "Logging in…";
  setStatus(status, "Connecting");
  try {
    const data = await api("/login", {
      method: "POST",
      body: JSON.stringify({ username: $("#username").value.trim(), password: $("#password").value }),
    });
    const success = data.status === "success";
    setStatus(status, success ? "Session active" : "Login failed", success ? "online" : "offline");
    if (success) $("#password").value = "";
    showToast(data.message, !success);
  } catch (error) {
    setStatus(status, "Login failed", "offline");
    showToast(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = "Login session";
  }
});

$("#detect-location").addEventListener("click", () => {
  if (!navigator.geolocation) {
    showToast("Geolocation is not available in this browser", true);
    return;
  }
  const button = $("#detect-location");
  button.disabled = true;
  button.textContent = "Detecting…";
  navigator.geolocation.getCurrentPosition(
    ({ coords }) => {
      $("#latitude").value = coords.latitude.toFixed(6);
      $("#longitude").value = coords.longitude.toFixed(6);
      button.disabled = false;
      button.textContent = "Use current location";
      showToast("Current location filled in");
    },
    (error) => {
      button.disabled = false;
      button.textContent = "Use current location";
      showToast(error.message, true);
    },
    { enableHighAccuracy: true, timeout: 10000 },
  );
});

$("#location-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $("#location-button");
  const status = $("#location-status");
  const result = $("#location-result");
  button.disabled = true;
  button.textContent = "Validating…";
  setStatus(status, "Checking");
  try {
    const data = await api("/cek-lokasi", {
      method: "POST",
      body: JSON.stringify({ latitude: $("#latitude").value, longitude: $("#longitude").value }),
    });
    const success = data.success === true;
    setStatus(status, success ? "Validated" : "Rejected", success ? "online" : "offline");
    result.hidden = false;
    result.classList.toggle("is-error", !success);
    result.textContent = data.message || data.error || "Location request completed";
  } catch (error) {
    setStatus(status, "Failed", "offline");
    result.hidden = false;
    result.classList.add("is-error");
    result.textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = "Validate location";
  }
});

$("#clear-results").addEventListener("click", () => {
  requests.forEach(({ id }) => {
    const card = resultCard(id);
    card.classList.remove("is-fetching", "has-data", "has-error");
    $(".result-state", card).textContent = "Waiting";
    const body = $(".result-body", card);
    body.className = "result-body empty-state";
    body.textContent = "No data collected yet.";
  });
  window.MyBestMotion?.setProgress(progress, 0);
  $("#gather-note").textContent = "Login first for protected data.";
  showToast("Collected data cleared");
});

checkHealth();
