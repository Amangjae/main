const API_BASE = '/api';

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

async function apiCall(endpoint, method = 'GET', payload = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };

  if (payload && method !== 'GET') {
    options.body = JSON.stringify(payload);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || `API 요청 실패 (${response.status})`);
  }
  return data;
}

function setStatus(type, message) {
  const node = document.getElementById('status-message');
  node.className = `status-message ${type}`;
  node.textContent = message;
}

function clearStatusLater() {
  window.clearTimeout(window.__statusTimer);
  window.__statusTimer = window.setTimeout(() => {
    const node = document.getElementById('status-message');
    node.className = 'status-message';
    node.textContent = '';
  }, 3000);
}

function fillAddressInput(address) {
  document.getElementById('base-address-input').value = address || '';
}

function renderConfig(config) {
  document.getElementById('config-info').textContent =
    `기준 주소: ${config.base_address} | 반경 ${config.search_radius_meters}m`;
  fillAddressInput(config.base_address);

  const apiButton = document.getElementById('external-api-btn');
  apiButton.disabled = !config.has_kakao_api;
  apiButton.title = config.has_kakao_api ? '' : 'KAKAO_REST_API_KEY가 없어 비활성화되었습니다.';
}

function renderWeather(weather) {
  const iconMap = {
    rainy: '☔',
    clear: '☀',
    hot: '🌡',
    cold: '❄',
    unknown: '⛅',
  };

  document.getElementById('weather-content').innerHTML = `
    <div class="weather-row">
      <div class="weather-main">
        <div class="weather-icon">${iconMap[weather.category] || '⛅'}</div>
        <div>
          <strong>오늘 점심 날씨: ${escapeHtml(weather.summary)}</strong>
          <p>기온 ${escapeHtml(weather.temperature_c)}°C</p>
          <p>${escapeHtml(weather.note)}</p>
        </div>
      </div>
      <div class="api-badge">${escapeHtml(weather.dong_name || '동 정보 없음')}</div>
    </div>
  `;
}

function recommendationCard(item) {
  const calories = item.estimated_calories ? `${item.estimated_calories}kcal` : '추정 불가';
  return `
    <article class="card restaurant-card">
      <div class="pill">${escapeHtml(item.recommendation_type)}</div>
      <h3>${escapeHtml(item.name)}</h3>
      <dl class="meta-grid">
        <div><dt>카테고리</dt><dd>${escapeHtml(item.category)}</dd></div>
        <div><dt>거리</dt><dd>${escapeHtml(item.distance_m)}m</dd></div>
        <div><dt>점수</dt><dd>${escapeHtml(item.score)}</dd></div>
        <div><dt>예산</dt><dd>${escapeHtml(item.price_level)}</dd></div>
        <div><dt>메인 메뉴</dt><dd>${escapeHtml(item.main_menu || '추정 불가')}</dd></div>
        <div><dt>칼로리</dt><dd>${escapeHtml(calories)}</dd></div>
      </dl>
      <p class="reason">${escapeHtml(item.reason)}</p>
      <button class="action-button" onclick="selectRestaurant(${item.id}, '${escapeHtml(item.name)}')">선택</button>
    </article>
  `;
}

function renderRecommendations(items) {
  const node = document.getElementById('recommendations');
  if (!items.length) {
    node.innerHTML = '<p class="loading">추천할 식당이 없습니다.</p>';
    return;
  }
  node.innerHTML = items.map((item) => recommendationCard(item)).join('');
}

function renderVisits(visits) {
  const node = document.getElementById('visits');
  if (!visits.length) {
    node.innerHTML = '<p class="loading">아직 방문 기록이 없습니다.</p>';
    return;
  }

  node.innerHTML = visits
    .map(
      (visit) => `
        <div class="list-item">
          <strong>${escapeHtml(visit.restaurant_name)}</strong>
          <span>${escapeHtml(visit.visited_on)} · ${escapeHtml(visit.meal_type)} · 당일 ${escapeHtml(visit.visit_count)}회 · 누적 ${escapeHtml(visit.total_visit_count)}회</span>
        </div>
      `
    )
    .join('');
}

async function loadAllData() {
  const [config, weather, recommendationsPayload, visitsPayload] = await Promise.all([
    apiCall('/config'),
    apiCall('/weather'),
    apiCall('/recommendations'),
    apiCall('/visits'),
  ]);

  renderConfig(config);
  renderWeather(weather);
  renderRecommendations(recommendationsPayload.recommendations || []);
  renderVisits(visitsPayload.visits || []);
}

async function applyBaseAddress() {
  const address = document.getElementById('base-address-input').value.trim();
  if (!address) {
    setStatus('error', '기준 주소를 입력해 주세요.');
    return;
  }

  try {
    setStatus('saving', '기준 주소를 적용하는 중입니다...');
    await apiCall('/base-address', 'POST', { address });
    await loadAllData();
    setStatus('success', '기준 주소를 적용했습니다.');
    clearStatusLater();
  } catch (error) {
    setStatus('error', error.message);
  }
}

async function connectExternalApi() {
  try {
    setStatus('saving', '카카오 API로 주변 식당을 가져오는 중입니다...');
    const result = await apiCall('/import-kakao', 'POST');
    await loadAllData();
    setStatus('success', `외부 API 연결 완료 · 신규 ${result.inserted}곳 · 중복 ${result.skipped}곳`);
    clearStatusLater();
  } catch (error) {
    setStatus('error', error.message);
  }
}

async function selectRestaurant(restaurantId, restaurantName) {
  try {
    setStatus('saving', `${restaurantName} 방문 기록을 저장하는 중입니다...`);
    await apiCall(`/visit/${restaurantId}`, 'POST');
    await loadAllData();
    setStatus('success', `${restaurantName} 방문 기록을 저장했습니다.`);
    clearStatusLater();
  } catch (error) {
    setStatus('error', error.message);
  }
}

async function refreshData() {
  try {
    setStatus('saving', '데이터를 새로고침하는 중입니다...');
    await loadAllData();
    setStatus('success', '데이터를 새로고침했습니다.');
    clearStatusLater();
  } catch (error) {
    setStatus('error', error.message);
  }
}

async function clearCache() {
  try {
    setStatus('saving', '서버 캐시를 비우는 중입니다...');
    const result = await apiCall('/clear-cache', 'POST');
    await loadAllData();
    setStatus('success', result.message);
    clearStatusLater();
  } catch (error) {
    setStatus('error', error.message);
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  try {
    await loadAllData();
  } catch (error) {
    setStatus('error', error.message);
  }
});
