const API_BASE = '/api';

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

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

async function loadConfig() {
  const config = await apiCall('/config');
  document.getElementById('config-info').textContent =
    `기준 주소: ${config.base_address} | 반경 ${config.search_radius_meters}m`;

  const kakaoBtn = document.getElementById('kakao-btn');
  kakaoBtn.disabled = !config.has_kakao_api;
  if (!config.has_kakao_api) {
    kakaoBtn.title = 'KAKAO_REST_API_KEY가 없어 비활성화되었습니다.';
  }
}

async function loadWeather() {
  const data = await apiCall('/weather');
  const iconMap = {
    rainy: '🌧️',
    clear: '🌤️',
    hot: '☀️',
    cold: '🥶',
    unknown: '🌥️',
  };

  document.getElementById('weather-content').innerHTML = `
    <div class="weather-row">
      <div class="weather-icon">${iconMap[data.category] || '🌥️'}</div>
      <div>
        <strong>오늘 점심 날씨: ${escapeHtml(data.summary)}</strong>
        <p>기온 ${escapeHtml(data.temperature_c)}°C</p>
        <p>${escapeHtml(data.note)}</p>
      </div>
    </div>
  `;
}

async function loadRecommendations() {
  const data = await apiCall('/recommendations');
  const list = data.recommendations || [];
  const node = document.getElementById('recommendations');

  if (!list.length) {
    node.innerHTML = '<p class="loading">추천할 식당이 없습니다.</p>';
    return;
  }

  node.innerHTML = list.map((item) => `
    <article class="card restaurant-card">
      <div class="pill">${escapeHtml(item.recommendation_type)}</div>
      <h3>${escapeHtml(item.name)}</h3>
      <dl class="meta-grid">
        <div><dt>카테고리</dt><dd>${escapeHtml(item.category)}</dd></div>
        <div><dt>거리</dt><dd>${escapeHtml(item.distance_m)}m</dd></div>
        <div><dt>점수</dt><dd>${escapeHtml(item.score)}</dd></div>
        <div><dt>예산</dt><dd>${escapeHtml(item.price_level)}</dd></div>
      </dl>
      <p class="reason">${escapeHtml(item.reason)}</p>
      <button class="secondary-button" onclick="recordVisit(${item.id}, '${escapeHtml(item.name)}')">방문 기록 추가</button>
    </article>
  `).join('');
}

async function loadVisits() {
  const data = await apiCall('/visits');
  const list = data.visits || [];
  const node = document.getElementById('visits');

  if (!list.length) {
    node.innerHTML = '<p class="loading">아직 방문 이력이 없습니다.</p>';
    return;
  }

  node.innerHTML = list.map((visit) => `
    <div class="list-item">
      <strong>${escapeHtml(visit.restaurant_name)}</strong>
      <span>${escapeHtml(visit.visited_on)} · ${escapeHtml(visit.meal_type)} · 누적 ${escapeHtml(visit.visit_count)}회</span>
    </div>
  `).join('');
}

async function loadRestaurants() {
  const data = await apiCall('/restaurants');
  const list = data.restaurants || [];
  const node = document.getElementById('restaurants');

  if (!list.length) {
    node.innerHTML = '<p class="loading">등록된 식당이 없습니다.</p>';
    return;
  }

  node.innerHTML = [`<p class="muted">총 ${data.count}곳</p>`].concat(
    list.map((restaurant) => {
      const address = restaurant.road_address || restaurant.address || '-';
      const link = restaurant.place_url
        ? `<a href="${escapeHtml(restaurant.place_url)}" target="_blank" rel="noreferrer">상세 보기</a>`
        : '';
      return `
        <div class="list-item">
          <strong>${escapeHtml(restaurant.name)}</strong>
          <span>${escapeHtml(restaurant.category)} · ${escapeHtml(restaurant.distance_m)}m · ${escapeHtml(address)}</span>
          <span class="source">source=${escapeHtml(restaurant.source || 'sample')} ${link}</span>
        </div>
      `;
    })
  ).join('');
}

async function loadAllData() {
  await Promise.all([loadConfig(), loadWeather(), loadRecommendations(), loadVisits(), loadRestaurants()]);
}

async function recordVisit(restaurantId, restaurantName) {
  try {
    setStatus('saving', `${restaurantName} 방문 기록을 저장하는 중입니다...`);
    await apiCall(`/visit/${restaurantId}`, 'POST');
    setStatus('success', `${restaurantName} 방문 이력을 저장했습니다.`);
    await Promise.all([loadRecommendations(), loadVisits()]);
    clearStatusLater();
  } catch (error) {
    setStatus('error', error.message);
  }
}

async function importFromKakao() {
  try {
    setStatus('saving', '카카오 API에서 주변 식당을 가져오는 중입니다...');
    const result = await apiCall('/import-kakao', 'POST');
    setStatus('success', `새로 추가 ${result.inserted}곳, 중복 건너뜀 ${result.skipped}곳`);
    await Promise.all([loadRestaurants(), loadRecommendations()]);
    clearStatusLater();
  } catch (error) {
    setStatus('error', error.message);
  }
}

async function resetData() {
  try {
    setStatus('saving', '샘플 데이터를 다시 세팅하는 중입니다...');
    const result = await apiCall('/reset-data', 'POST');
    setStatus('success', result.message);
    await loadAllData();
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
    setStatus('success', result.message);
    await loadAllData();
    clearStatusLater();
  } catch (error) {
    setStatus('error', error.message);
  }
}

function toggleRestaurants() {
  document.getElementById('restaurants-wrapper').classList.toggle('collapsed');
}

document.addEventListener('DOMContentLoaded', async () => {
  try {
    await loadAllData();
  } catch (error) {
    setStatus('error', error.message);
  }

  window.setInterval(() => {
    loadRecommendations().catch(() => {});
    loadVisits().catch(() => {});
  }, 5 * 60 * 1000);
});
