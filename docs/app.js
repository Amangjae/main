const DATA_URL = window.LUNCH_DATA_URL || "./data/site-data.json";
const SHEET_URL = window.LUNCH_SHEET_URL || "";

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

function calculateWalkMinutes(distanceValue) {
  const distance = Number(distanceValue);

  if (!Number.isFinite(distance) || distance <= 0) {
    return null;
  }

  return Math.max(1, Math.round(distance / 75));
}

function formatDistance(distanceValue) {
  const distance = Number(distanceValue);

  if (!Number.isFinite(distance) || distance < 0) {
    return "거리 정보 없음";
  }

  const walkMinutes = calculateWalkMinutes(distance);

  return walkMinutes
    ? `${distance.toLocaleString("ko-KR")}m · 도보 약 ${walkMinutes}분`
    : `${distance.toLocaleString("ko-KR")}m`;
}

function formatTemperature(value) {
  const temperature = Number(value);

  if (!Number.isFinite(temperature)) {
    return "-";
  }

  return Number.isInteger(temperature)
    ? String(temperature)
    : temperature.toFixed(1);
}

function normalizeRecommendationType(value) {
  return String(value || "오늘의 추천").trim() || "오늘의 추천";
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

async function loadData() {
  const response = await fetch(`${DATA_URL}?t=${Date.now()}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(
      `데이터 파일을 불러오지 못했습니다. (${response.status})`,
    );
  }

  return response.json();
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

    if (node?.classList.contains("success")) {
      node.textContent = "";
      node.className = "status-message";
    }
  }, delay);
}

function renderConfig(data) {
  const title = data.title || "오늘 뭐 먹지?";
  const address = data.base_address || "기준 주소 없음";
  const radius = Number(data.search_radius_meters || 1500);
  const radiusText = Number.isFinite(radius)
    ? radius >= 1000
      ? `${(radius / 1000).toFixed(radius % 1000 === 0 ? 0 : 1)}km`
      : `${radius}m`
    : "반경 정보 없음";

  document.title = title;

  document.getElementById("config-info").textContent =
    `${data.dong_name || "기준 지역"} 주변의 식당 중 날씨, 거리, 방문 기록을 반영해 추천합니다.`;

  document.getElementById("base-address-input").value = address;
  document.getElementById("radius-input").value = radiusText;

  document.getElementById("location-summary-value").textContent =
    `${address} · 반경 ${radiusText}`;

  document.getElementById("generated-at").textContent =
    formatGeneratedAt(data.generated_at);

  const sheetButton = document.getElementById("sheet-open-btn");
  const sheetUrl = data.sheet_url || SHEET_URL;

  sheetButton.dataset.sheetUrl = sheetUrl;
  sheetButton.disabled = !safeExternalUrl(sheetUrl);
}

function renderWeather(data) {
  const weather = data.weather || {};

  const iconMap = {
    rainy: "☔",
    clear: "☀️",
    hot: "🌡️",
    cold: "❄️",
    cloudy: "☁️",
    snow: "🌨️",
    unknown: "⛅",
  };

  const category = weather.category || "unknown";
  const summary = weather.summary || "날씨 정보 없음";
  const note =
    weather.note ||
    "날씨와 이동 거리를 함께 고려해 오늘의 식당을 추천했습니다.";
  const temperature = formatTemperature(weather.temperature_c);

  document.getElementById("weather-content").innerHTML = `
    <div class="weather-row">
      <div class="weather-main">
        <div class="weather-icon" aria-hidden="true">
          ${iconMap[category] || "⛅"}
        </div>

        <div class="weather-copy">
          <strong>${escapeHtml(summary)}</strong>
          <p class="weather-temperature">${escapeHtml(temperature)}°C</p>
          <p class="weather-note">${escapeHtml(note)}</p>
        </div>
      </div>

      <div class="api-badge">
        ${escapeHtml(data.dong_name || "지역 정보 없음")}
      </div>
    </div>
  `;
}

function recommendationCard(item, index) {
  const name = item.name || "식당명 없음";
  const recommendationType = normalizeRecommendationType(
    item.recommendation_type,
  );
  const category = normalizeCategory(item.category);
  const mainMenu = item.main_menu || "대표 메뉴 정보 없음";
  const priceLevel = item.price_level || "가격 정보 없음";
  const calories = item.estimated_calories
    ? `${item.estimated_calories}kcal`
    : "칼로리 정보 없음";
  const distanceText = formatDistance(item.distance_m);
  const reason =
    item.reason ||
    "거리와 방문 기록을 바탕으로 오늘의 추천 식당으로 선정했습니다.";
  const placeUrl = safeExternalUrl(item.place_url);
  const score = item.score ?? "-";

  const mapButton = placeUrl
    ? `
      <a
        class="map-button"
        href="${escapeHtml(placeUrl)}"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="${escapeHtml(name)} 카카오맵에서 보기"
      >
        카카오맵 보기
      </a>
    `
    : `
      <button
        class="secondary-button"
        type="button"
        disabled
        aria-label="지도 주소 없음"
      >
        지도 정보 없음
      </button>
    `;

  return `
    <article class="card restaurant-card">
      <div class="card-topline">
        <div class="badge-group">
          <span class="pill">${escapeHtml(recommendationType)}</span>
          <span class="category-pill">${escapeHtml(category)}</span>
        </div>

        <span class="score-note">추천 ${index + 1}</span>
      </div>

      <h3>${escapeHtml(name)}</h3>

      <p class="main-menu">
        ${escapeHtml(mainMenu)}
      </p>

      <dl class="meta-grid">
        <div class="meta-item">
          <dt>거리</dt>
          <dd>${escapeHtml(distanceText)}</dd>
        </div>

        <div class="meta-item">
          <dt>예상 가격</dt>
          <dd>${escapeHtml(priceLevel)}</dd>
        </div>

        <div class="meta-item">
          <dt>음식 분류</dt>
          <dd>${escapeHtml(category)}</dd>
        </div>

        <div class="meta-item">
          <dt>참고 정보</dt>
          <dd>${escapeHtml(calories)}</dd>
        </div>
      </dl>

      <div class="reason-box">
        <span class="reason-label">추천 이유</span>
        <p class="reason">${escapeHtml(reason)}</p>
      </div>

      <div class="card-actions">
        ${mapButton}
      </div>

      <span class="visually-hidden">내부 추천 점수 ${escapeHtml(score)}</span>
    </article>
  `;
}

function renderRecommendations(items) {
  const node = document.getElementById("recommendations");

  if (!Array.isArray(items) || items.length === 0) {
    node.innerHTML =
      '<p class="loading">현재 추천할 수 있는 식당이 없습니다.</p>';
    return;
  }

  node.innerHTML = items
    .slice(0, 4)
    .map((item, index) => recommendationCard(item, index))
    .join("");
}

function renderVisits(visits) {
  const node = document.getElementById("visits");

  if (!Array.isArray(visits) || visits.length === 0) {
    node.innerHTML =
      '<p class="loading">아직 등록된 방문 기록이 없습니다.</p>';
    return;
  }

  node.innerHTML = visits
    .slice(0, 5)
    .map((visit) => {
      const restaurantName =
        visit.restaurant_name || "식당명 없음";
      const visitedOn = visit.visited_on || "날짜 없음";
      const mealType = visit.meal_type || "식사";
      const latestVisitCount = Number(visit.visit_count || 0);
      const totalVisitCount = Number(
        visit.total_visit_count || latestVisitCount || 0,
      );

      return `
        <div class="list-item">
          <div class="list-item-main">
            <strong>${escapeHtml(restaurantName)}</strong>
            <span>
              ${escapeHtml(visitedOn)} · ${escapeHtml(mealType)}
              ${
                latestVisitCount > 0
                  ? ` · 해당 기록 ${escapeHtml(latestVisitCount)}회`
                  : ""
              }
            </span>
          </div>

          <span class="visit-count">
            누적 ${escapeHtml(totalVisitCount)}회
          </span>
        </div>
      `;
    })
    .join("");
}

function toggleSettings() {
  const panel = document.getElementById("settings-panel");
  const button = document.getElementById("settings-toggle-btn");
  const isOpen = !panel.hidden;

  panel.hidden = isOpen;
  button.setAttribute("aria-expanded", String(!isOpen));
  button.textContent = isOpen ? "설정 보기" : "설정 닫기";
}

function openSheet() {
  const button = document.getElementById("sheet-open-btn");
  const sheetUrl = safeExternalUrl(
    button.dataset.sheetUrl || SHEET_URL,
  );

  if (!sheetUrl) {
    setStatus(
      "error",
      "구글 시트 주소가 아직 설정되지 않았습니다.",
    );
    return;
  }

  window.open(sheetUrl, "_blank", "noopener,noreferrer");
}

async function renderAllData() {
  const data = await loadData();

  renderConfig(data);
  renderWeather(data);
  renderRecommendations(data.recommendations || []);
  renderVisits(data.visits || []);
}

async function refreshData() {
  const refreshButton = document.getElementById("refresh-btn");

  try {
    refreshButton.disabled = true;
    refreshButton.textContent = "불러오는 중";

    setStatus("saving", "최신 데이터를 불러오는 중입니다.");

    await renderAllData();

    setStatus("success", "최신 데이터로 새로고침했습니다.");
    clearStatusLater();
  } catch (error) {
    console.error(error);

    setStatus(
      "error",
      error instanceof Error
        ? error.message
        : "데이터를 불러오는 중 오류가 발생했습니다.",
    );
  } finally {
    refreshButton.disabled = false;
    refreshButton.textContent = "새로고침";
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  document
    .getElementById("settings-toggle-btn")
    .addEventListener("click", toggleSettings);

  document
    .getElementById("sheet-open-btn")
    .addEventListener("click", openSheet);

  document
    .getElementById("refresh-btn")
    .addEventListener("click", refreshData);

  try {
    setStatus("saving", "점심 추천 데이터를 불러오는 중입니다.");

    await renderAllData();

    setStatus("success", "오늘의 점심 추천을 불러왔습니다.");
    clearStatusLater();
  } catch (error) {
    console.error(error);

    setStatus(
      "error",
      error instanceof Error
        ? error.message
        : "페이지 데이터를 불러오지 못했습니다.",
    );
  }
});