const DATA_URL = window.LUNCH_DATA_URL || "./data/site-data.json";
const SHEET_URL = window.LUNCH_SHEET_URL || "";
const ACTION_API_URL = window.LUNCH_ACTION_API_URL || "";
const RECENT_EXCLUDE_DAYS = 7;

const state = {
  data: null,
  partySize: 2,
  submittedToday: false,
};

function updateDecisionButtons() {
  const skipButton = document.getElementById("skip-day-btn");
  if (skipButton) {
    skipButton.disabled = state.submittedToday;
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function safeExternalUrl(value) {
  try {
    const url = new URL(String(value || ""));
    if (!["http:", "https:"].includes(url.protocol)) {
      return "";
    }
    return url.href;
  } catch {
    return "";
  }
}

function setStatus(type, message) {
  const node = document.getElementById("status-message");
  if (!node) {
    return;
  }
  node.className = `status-message ${type || ""}`.trim();
  node.textContent = message || "";
}

function clearStatusLater(delay = 2500) {
  window.setTimeout(() => {
    const node = document.getElementById("status-message");
    if (node && node.classList.contains("success")) {
      node.className = "status-message";
      node.textContent = "";
    }
  }, delay);
}

function formatGeneratedAt(value) {
  if (!value) {
    return "업데이트 시간 없음";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return `업데이트: ${value}`;
  }
  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function formatDistance(distanceValue) {
  const distance = Number(distanceValue);
  if (!Number.isFinite(distance) || distance < 0) {
    return "거리 정보 없음";
  }
  const walkMinutes = Math.max(1, Math.round(distance / 75));
  return `${distance.toLocaleString("ko-KR")}m · 도보 약 ${walkMinutes}분`;
}

function formatRadius(radius) {
  const value = Number(radius);
  if (!Number.isFinite(value)) {
    return "반경 정보 없음";
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(value % 1000 === 0 ? 0 : 1)}km`;
  }
  return `${value}m`;
}

function formatCalories(value) {
  const calories = Number(value);
  if (!Number.isFinite(calories) || calories <= 0) {
    return "칼로리 정보 없음";
  }
  return `${calories.toLocaleString("ko-KR")}kcal`;
}

function getTodayString() {
  return new Date().toLocaleDateString("sv-SE", { timeZone: "Asia/Seoul" });
}

function getLocalDecisionKey() {
  return `lunch-decision-${getTodayString()}`;
}

function readSubmittedToday() {
  return localStorage.getItem(getLocalDecisionKey()) === "done";
}

function rememberSubmittedToday() {
  localStorage.setItem(getLocalDecisionKey(), "done");
  state.submittedToday = true;
}

function parseVisitDate(value) {
  if (!value) {
    return null;
  }
  const plain = String(value).slice(0, 10);
  const date = new Date(`${plain}T00:00:00+09:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}

function daysSince(value) {
  const date = parseVisitDate(value);
  if (!date) {
    return 999;
  }
  const now = new Date(`${getTodayString()}T00:00:00+09:00`);
  return Math.floor((now - date) / 86400000);
}

function normalizeCategory(value) {
  const category = String(value || "").trim();
  if (!category) {
    return "분류 없음";
  }
  const parts = category
    .split(">")
    .map((part) => part.trim())
    .filter(Boolean);
  return parts.at(-1) || category;
}

function weatherBonus(restaurant, weather) {
  const category = String(weather?.category || "clear");
  const indoor = Number(restaurant.indoor_score || 3);
  const soup = Number(restaurant.soup_score || 2);
  const noodle = Number(restaurant.noodle_score || 2);
  const rice = Number(restaurant.rice_score || 2);

  if (category === "rainy") {
    return {
      score: indoor * 0.9 + soup * 0.6,
      reason: "비 오는 날이라 실내 식사와 국물 메뉴에 가점을 줬습니다.",
    };
  }
  if (category === "hot") {
    return {
      score: indoor * 0.7 + noodle * 0.5,
      reason: "더운 날이라 시원하게 먹기 쉬운 메뉴와 실내 좌석을 반영했습니다.",
    };
  }
  if (category === "cold") {
    return {
      score: soup * 0.9 + rice * 0.4,
      reason: "추운 날이라 든든한 식사와 국물 메뉴에 가점을 줬습니다.",
    };
  }
  return {
    score: rice * 0.4,
    reason: "무난한 날씨라 평소 점심으로 먹기 편한 메뉴를 반영했습니다.",
  };
}

function partySizeBonus(restaurant, partySize) {
  const minimum = Number(restaurant.party_size_min || 1);
  const maximum = Number(restaurant.party_size_max || 4);

  if (partySize >= minimum && partySize <= maximum) {
    return {
      score: 1.6,
      reason: `${partySize}명 식사에 비교적 잘 맞는 곳입니다.`,
    };
  }
  if (partySize < minimum) {
    return {
      score: -1.4,
      reason: `${partySize}명이 가기엔 조금 큰 매장으로 판단했습니다.`,
    };
  }
  return {
    score: -2.2,
    reason: `${partySize}명이 가기엔 좌석 여유가 부족할 수 있습니다.`,
  };
}

function buildVisitIndex(visits) {
  const index = new Map();
  for (const visit of visits || []) {
    if ((visit.decision || "selected") !== "selected") {
      continue;
    }
    const key =
      String(visit.restaurant_id || "").trim() ||
      String(visit.restaurant_key || "").trim() ||
      String(visit.restaurant_name || "").trim();
    if (!key) {
      continue;
    }
    const current = index.get(key) || {
      restaurant_name: visit.restaurant_name || "",
      total_visits: 0,
      last_selected_on: "",
    };
    current.total_visits += 1;
    const visitedOn = String(visit.date || visit.visited_on || visit.selected_at || "").trim();
    if (visitedOn && visitedOn > current.last_selected_on) {
      current.last_selected_on = visitedOn;
    }
    index.set(key, current);
  }
  return index;
}

function historyScore(totalVisits, lastSelectedOn) {
  if (totalVisits <= 0) {
    return {
      score: 1.2,
      reason: "아직 선택 기록이 적어서 새로운 후보로 올렸습니다.",
    };
  }
  const diff = daysSince(lastSelectedOn);
  if (diff <= RECENT_EXCLUDE_DAYS) {
    return {
      score: -5,
      reason: "최근 1주일 안에 선택된 식당이라 우선 제외 대상입니다.",
    };
  }
  return {
    score: Math.min(totalVisits * 0.35, 1.8) + Math.min(diff / 12, 2.8),
    reason: `최근 방문 후 ${diff}일 지나 다시 가도 부담이 적습니다.`,
  };
}

function portalSearchUrl(item) {
  const query = `${item.name || ""} ${item.address || ""}`.trim();
  return `https://search.naver.com/search.naver?where=nexearch&query=${encodeURIComponent(query)}`;
}

function mapUrl(item) {
  return safeExternalUrl(item.place_url);
}

function computeRecommendations(data, partySize) {
  const visitIndex = buildVisitIndex(data.visit_history || []);
  const visited = [];
  const fresh = [];

  for (const restaurant of data.restaurants || []) {
    const restaurantId =
      String(restaurant.external_id || "").trim() ||
      String(restaurant.kakao_place_id || "").trim() ||
      String(restaurant.name || "").trim();
    if (!restaurantId) {
      continue;
    }

    const history =
      visitIndex.get(restaurantId) ||
      visitIndex.get(String(restaurant.name || "").trim()) || {
        total_visits: 0,
        last_selected_on: "",
      };

    if (history.total_visits > 0 && daysSince(history.last_selected_on) <= RECENT_EXCLUDE_DAYS) {
      continue;
    }

    const weather = weatherBonus(restaurant, data.weather || {});
    const party = partySizeBonus(restaurant, partySize);
    const historyPart = historyScore(history.total_visits || 0, history.last_selected_on || "");
    const distanceScore = Math.max(0, 2.2 - Number(restaurant.distance_m || 0) / 900);
    const score = weather.score + party.score + historyPart.score + distanceScore;

    const item = {
      id: restaurantId,
      name: restaurant.name || "식당명 없음",
      category: restaurant.category || "",
      main_menu: restaurant.main_menu || "대표 메뉴 정보 없음",
      estimated_calories: Number(restaurant.estimated_calories || 0),
      distance_m: Number(restaurant.distance_m || 0),
      price_level: restaurant.price_level || "보통",
      party_size_min: Number(restaurant.party_size_min || 1),
      party_size_max: Number(restaurant.party_size_max || 4),
      address: restaurant.road_address || restaurant.address || "",
      place_url: restaurant.place_url || "",
      score,
      reason: [
        weather.reason,
        historyPart.reason,
        party.reason,
        `기준 주소에서 약 ${Number(restaurant.distance_m || 0)}m 거리입니다.`,
      ].join(" / "),
      total_visits: Number(history.total_visits || 0),
    };

    if (item.total_visits > 0) {
      visited.push(item);
    } else {
      fresh.push(item);
    }
  }

  visited.sort((a, b) => b.score - a.score || a.distance_m - b.distance_m || a.name.localeCompare(b.name));
  fresh.sort((a, b) => b.score - a.score || a.distance_m - b.distance_m || a.name.localeCompare(b.name));

  const selected = [];
  for (const item of visited.slice(0, 3)) {
    item.recommendation_type = "다시 가도 좋은 곳";
    selected.push(item);
  }
  for (const item of fresh.slice(0, 1)) {
    item.recommendation_type = "새로운 후보";
    selected.push(item);
  }

  const remaining = [...visited.slice(3), ...fresh.slice(1)];
  for (const item of remaining) {
    if (selected.includes(item)) {
      continue;
    }
    item.recommendation_type = item.recommendation_type || "추가 후보";
    selected.push(item);
    if (selected.length >= 4) {
      break;
    }
  }
  return selected.slice(0, 4);
}

function renderConfig(data) {
  document.title = data.title || "점심 추천";
  const radiusText = formatRadius(data.search_radius_meters);
  document.getElementById("config-info").textContent = `${
    data.dong_name || "기준 위치"
  } 주변 식당을 기준으로 날씨, 최근 방문 기록, 참석 인원을 함께 반영합니다.`;
  document.getElementById("base-address-input").value = data.base_address || "";
  document.getElementById("radius-input").value = radiusText;
  document.getElementById("generated-at").textContent = formatGeneratedAt(data.generated_at);

  const select = document.getElementById("party-size-select");
  const defaultPartySize = Number(data.party_size_default || 2);
  state.partySize = defaultPartySize;
  select.value = String(defaultPartySize >= 5 ? 5 : defaultPartySize);

  const sheetButton = document.getElementById("sheet-open-btn");
  const sheetUrl = safeExternalUrl(data.sheet_url || SHEET_URL);
  sheetButton.disabled = !sheetUrl;
  sheetButton.dataset.sheetUrl = sheetUrl;
}

function renderWeather(data) {
  const weather = data.weather || {};
  const iconMap = {
    rainy: "☔",
    clear: "☀️",
    hot: "🌡️",
    cold: "🧣",
    cloudy: "☁️",
    unknown: "🍽️",
  };

  document.getElementById("weather-content").innerHTML = `
    <div class="weather-row">
      <div class="weather-main">
        <div class="weather-icon" aria-hidden="true">${iconMap[weather.category] || "🍽️"}</div>
        <div class="weather-copy">
          <strong>${escapeHtml(weather.summary || "날씨 정보 없음")}</strong>
          <p class="weather-temperature">${escapeHtml(String(weather.temperature_c ?? "-"))}°C</p>
          <p class="weather-note">${escapeHtml(weather.note || "")}</p>
        </div>
      </div>
      <div class="api-badge">${escapeHtml(data.dong_name || "기준 위치")}</div>
    </div>
  `;
}

function recommendationCard(item, index) {
  const searchUrl = portalSearchUrl(item);
  const placeUrl = mapUrl(item);
  const disabled = state.submittedToday ? "disabled" : "";

  return `
    <article class="card restaurant-card">
      <div class="card-topline">
        <div class="badge-group">
          <span class="pill">${escapeHtml(item.recommendation_type || "추천")}</span>
          <span class="category-pill">${escapeHtml(normalizeCategory(item.category))}</span>
        </div>
        <span class="score-note">추천 ${index + 1}</span>
      </div>

      <h3>${escapeHtml(item.name)}</h3>
      <p class="main-menu">${escapeHtml(item.main_menu || "대표 메뉴 정보 없음")}</p>

      <dl class="meta-grid">
        <div class="meta-item">
          <dt>거리</dt>
          <dd>${escapeHtml(formatDistance(item.distance_m))}</dd>
        </div>
        <div class="meta-item">
          <dt>예상 칼로리</dt>
          <dd>${escapeHtml(formatCalories(item.estimated_calories))}</dd>
        </div>
        <div class="meta-item">
          <dt>인원 추천</dt>
          <dd>${escapeHtml(`${item.party_size_min}~${item.party_size_max}명`)}</dd>
        </div>
        <div class="meta-item">
          <dt>주소</dt>
          <dd>${escapeHtml(item.address || "주소 정보 없음")}</dd>
        </div>
      </dl>

      <div class="reason-box">
        <span class="reason-label">추천 이유</span>
        <p class="reason">${escapeHtml(item.reason || "")}</p>
      </div>

      <div class="card-actions">
        <button
          class="primary-button select-button"
          type="button"
          data-restaurant-id="${escapeHtml(item.id)}"
          ${disabled}
        >
          선택
        </button>
        <a class="secondary-link" href="${escapeHtml(searchUrl)}" target="_blank" rel="noopener noreferrer">포털 검색</a>
        ${
          placeUrl
            ? `<a class="secondary-link" href="${escapeHtml(placeUrl)}" target="_blank" rel="noopener noreferrer">지도 보기</a>`
            : ""
        }
      </div>
    </article>
  `;
}

function renderRecommendations() {
  const node = document.getElementById("recommendations");
  const items = computeRecommendations(state.data, state.partySize);
  updateDecisionButtons();

  if (!items.length) {
    node.innerHTML = '<p class="loading">조건에 맞는 추천 식당이 없습니다. 참석 인원을 바꾸거나 내일 다시 확인해 주세요.</p>';
    return;
  }

  node.innerHTML = items.map((item, index) => recommendationCard(item, index)).join("");
  node.querySelectorAll(".select-button").forEach((button) => {
    button.addEventListener("click", () => {
      const restaurantId = button.dataset.restaurantId;
      const selected = items.find((item) => item.id === restaurantId);
      if (selected) {
        submitDecision("selected", selected);
      }
    });
  });
}

function renderVisits(data) {
  const node = document.getElementById("visits");
  const visits = Array.isArray(data.visits) ? data.visits : [];

  if (!visits.length) {
    node.innerHTML = '<p class="loading">아직 저장된 선택 기록이 없습니다.</p>';
    return;
  }

  node.innerHTML = visits
    .map(
      (visit) => `
        <div class="list-item">
          <div class="list-item-main">
            <strong>${escapeHtml(visit.restaurant_name || "식당명 없음")}</strong>
            <span>${escapeHtml(visit.visited_on || "")} · ${escapeHtml(
              visit.party_size ? `${visit.party_size}명` : "인원 미기록",
            )}</span>
          </div>
          <span class="visit-count">누적 ${escapeHtml(String(visit.visit_count || 0))}회</span>
        </div>
      `,
    )
    .join("");
}

async function loadData() {
  const response = await fetch(`${DATA_URL}?t=${Date.now()}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`데이터 파일을 불러오지 못했습니다. (${response.status})`);
  }
  return response.json();
}

async function renderAllData() {
  const data = await loadData();
  state.data = data;
  renderConfig(data);
  renderWeather(data);
  renderRecommendations();
  renderVisits(data);

  if (data.warning) {
    setStatus("saving", `참고: ${data.warning}`);
  }
}

function openSheet() {
  const button = document.getElementById("sheet-open-btn");
  const sheetUrl = safeExternalUrl(button.dataset.sheetUrl || SHEET_URL);
  if (!sheetUrl) {
    setStatus("error", "구글 시트 주소가 설정되지 않았습니다.");
    return;
  }
  window.open(sheetUrl, "_blank", "noopener,noreferrer");
}

async function refreshData() {
  const button = document.getElementById("refresh-btn");
  try {
    button.disabled = true;
    button.textContent = "불러오는 중";
    setStatus("saving", "최신 추천 데이터를 불러오는 중입니다.");
    await renderAllData();
    setStatus("success", "추천 데이터를 새로 불러왔습니다.");
    clearStatusLater();
  } catch (error) {
    console.error(error);
    setStatus("error", error instanceof Error ? error.message : "데이터를 불러오는 중 오류가 발생했습니다.");
  } finally {
    button.disabled = false;
    button.textContent = "추천 다시 불러오기";
  }
}

async function postSelection(payload) {
  const configuredUrl = safeExternalUrl(state.data?.selection_endpoint || ACTION_API_URL);
  if (!configuredUrl) {
    throw new Error("선택 저장용 Apps Script URL이 아직 설정되지 않았습니다.");
  }

  const response = await fetch(configuredUrl, {
    method: "POST",
    headers: { "Content-Type": "text/plain;charset=utf-8" },
    body: JSON.stringify(payload),
  });

  const text = await response.text();
  let result = {};
  try {
    result = text ? JSON.parse(text) : {};
  } catch {
    result = {};
  }

  if (!response.ok || result.ok === false) {
    throw new Error(result.message || "선택 내용을 저장하지 못했습니다.");
  }
}

async function submitDecision(decision, restaurant) {
  if (state.submittedToday) {
    setStatus("error", "오늘은 이미 선택이 저장되었습니다.");
    return;
  }

  const payload = {
    date: getTodayString(),
    decision,
    party_size: state.partySize,
    base_address: state.data?.base_address || "",
    dong_name: state.data?.dong_name || "",
    weather_summary: state.data?.weather?.summary || "",
    selected_at: new Date().toISOString(),
    restaurant_id: restaurant?.id || "",
    restaurant_name: restaurant?.name || "",
    place_url: restaurant?.place_url || "",
    main_menu: restaurant?.main_menu || "",
    estimated_calories: restaurant?.estimated_calories || 0,
  };

  try {
    setStatus("saving", decision === "selected" ? "선택 내용을 저장하는 중입니다." : "오늘 점심 안 감 기록을 저장하는 중입니다.");
    await postSelection(payload);
    rememberSubmittedToday();
    if (state.data) {
      const visitHistory = Array.isArray(state.data.visit_history) ? state.data.visit_history : [];
      visitHistory.unshift({
        date: payload.date,
        restaurant_id: payload.restaurant_id,
        restaurant_name: payload.restaurant_name,
        party_size: payload.party_size,
        decision: payload.decision,
        base_address: payload.base_address,
        dong_name: payload.dong_name,
        weather_summary: payload.weather_summary,
        selected_at: payload.selected_at,
        place_url: payload.place_url,
        main_menu: payload.main_menu,
        estimated_calories: payload.estimated_calories,
      });
      state.data.visit_history = visitHistory;
      if (decision === "selected") {
        const visits = Array.isArray(state.data.visits) ? state.data.visits : [];
        visits.unshift({
          restaurant_name: payload.restaurant_name,
          restaurant_id: payload.restaurant_id,
          visited_on: payload.date,
          visit_count: 1,
          party_size: payload.party_size,
        });
        state.data.visits = visits.slice(0, 5);
        renderVisits(state.data);
      }
    }
    updateDecisionButtons();
    renderRecommendations();
    setStatus("success", decision === "selected" ? "오늘 점심 선택이 저장되었습니다." : "오늘은 가지 않음 기록이 저장되었습니다.");
    clearStatusLater(3000);
  } catch (error) {
    console.error(error);
    setStatus("error", error instanceof Error ? error.message : "기록 저장 중 오류가 발생했습니다.");
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  state.submittedToday = readSubmittedToday();
  updateDecisionButtons();

  document.getElementById("party-size-select").addEventListener("change", (event) => {
    const value = Number(event.target.value || 2);
    state.partySize = value >= 5 ? 5 : value;
    if (state.data) {
      renderRecommendations();
    }
  });

  document.getElementById("sheet-open-btn").addEventListener("click", openSheet);
  document.getElementById("refresh-btn").addEventListener("click", refreshData);
  document.getElementById("skip-day-btn").addEventListener("click", () => submitDecision("skip_day", null));

  try {
    setStatus("saving", "점심 추천 데이터를 불러오는 중입니다.");
    await renderAllData();
    setStatus("success", "오늘의 점심 추천을 준비했습니다.");
    clearStatusLater();
  } catch (error) {
    console.error(error);
    setStatus("error", error instanceof Error ? error.message : "페이지 데이터를 불러오지 못했습니다.");
  }
});
