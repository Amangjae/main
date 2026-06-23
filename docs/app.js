const API_BASE = (window.LUNCH_API_BASE || '').replace(/\/$/, '');

const sampleWeather = {
  category: 'hot',
  summary: '덥고 습함',
  temperature_c: 29,
  note: '시원한 메뉴나 실내 식당이 잘 어울립니다.',
  dong_name: '을지로동',
};

const sampleVisits = [
  { restaurant_name: '을지로국밥', visited_on: '2026-06-20', meal_type: '점심', visit_count: 2, total_visit_count: 3 },
  { restaurant_name: '을지로중화반점', visited_on: '2026-06-18', meal_type: '점심', visit_count: 1, total_visit_count: 1 },
];

const sampleRecommendations = [
  { id: 1, name: '을지로국밥', category: '한식', distance_m: 250, score: 6.4, price_level: '보통', recommendation_type: '재방문 추천', reason: '더운 날씨를 고려했고, 가까우면서 든든한 식당입니다.', main_menu: '국밥', estimated_calories: 700 },
  { id: 2, name: '을지로제육식당', category: '한식', distance_m: 430, score: 5.8, price_level: '보통', recommendation_type: '재방문 추천', reason: '든든한 점심 메뉴이고 이동 부담이 적습니다.', main_menu: '제육볶음', estimated_calories: 820 },
  { id: 4, name: '을지로중화반점', category: '중식', distance_m: 640, score: 5.3, price_level: '보통', recommendation_type: '재방문 추천', reason: '실내 선호와 메뉴 다양성을 함께 반영했습니다.', main_menu: '짬뽕', estimated_calories: 800 },
  { id: 3, name: '을지로파스타랩', category: '양식', distance_m: 580, score: 4.9, price_level: '중간 이상', recommendation_type: '새로운 도전', reason: '아직 방문 이력이 없는 신규 후보입니다.', main_menu: '크림 파스타', estimated_calories: 850 },
];

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

async function apiCall(endpoint, method = 'GET', payload = null) {
  if (!API_BASE) {
    throw new Error('API 서버 주소가 설정되지 않았습니다.');
  }

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

function fillAddressInput(address) {
  document.getElementById('base-address-input').value = address || '';
}

function renderConfig(config) {
  document.getElementById('config-info').textContent =
    `기준 주소: ${config.base_address} | 반경 ${config.search_radius_meters}m`;
  fillAddressInput(config.base_address);
  document.getElementById('external-api-btn').disabled = !config.has_kakao_api;
}

function renderWeather(weather) {
  const iconMap = { rainy: '☔', clear: '☀', hot: '🌡', cold: '❄', unknown: '⛅' };
  const badgeText = weather.dong_name || '동 정보 없음';
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
      <div class="api-badge">${escapeHtml(badgeText)}</div>
    </div>
  `;
}

function recommendationCard(item, enableSelectButton) {
  const calories = item.estimated_calories ? `${item.estimated_calories}kcal` : '추정 불가';
  const buttonHtml = enableSelectButton
    ? `<button class="action-button" onclick="selectRestaurant(${item.id}, '${escapeHtml(item.name)}')">선택</button>`
    : '<button class="action-button" disabled>선택</button>';

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
      ${buttonHtml}
    </article>
  `;
}

function renderRecommendations(items, enableSelectButton) {
  const node = document.getElementById('recommendations');
  if (!items.length) {
    node.innerHTML = '<p class="loading">추천할 식당이 없습니다.</p>';
    return;
  }
  node.innerHTML = items.map((item) => recommendationCard(item, enableSelectButton)).join('');
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

async function loadLiveData() {
  const [config, weather, recommendationsPayload, visitsPayload] = await Promise.all([
    apiCall('/api/config'),
    apiCall('/api/weather'),
    apiCall('/api/recommendations'),
    apiCall('/api/visits'),
  ]);

  renderConfig(config);
  renderWeather(weather);
  renderRecommendations(recommendationsPayload.recommendations || [], true);
  renderVisits(visitsPayload.visits || []);
}

function loadSampleData() {
  renderConfig({ base_address: '서울특별시 중구 을지로 16', search_radius_meters: 1500, has_kakao_api: false });
  renderWeather(sampleWeather);
  renderRecommendations(sampleRecommendations, false);
  renderVisits(sampleVisits);
}

async function applyBaseAddress() {
  if (!API_BASE) {
    alert('외부 API 서버가 연결되어 있지 않습니다.');
    return;
  }

  const address = document.getElementById('base-address-input').value.trim();
  if (!address) {
    setStatus('error', '기준 주소를 입력해 주세요.');
    return;
  }

  try {
    await apiCall('/api/base-address', 'POST', { address });
    setStatus('success', '기준 주소를 적용했습니다.');
    await loadLiveData();
  } catch (error) {
    setStatus('error', error.message);
  }
}

async function connectExternalApi() {
  if (!API_BASE) {
    setStatus('error', 'docs/config.js에 외부 API 주소를 입력해 주세요.');
    return;
  }

  try {
    const result = await apiCall('/api/import-kakao', 'POST');
    setStatus('success', `외부 API 연결 완료 · 신규 ${result.inserted}곳 · 중복 ${result.skipped}곳`);
    await loadLiveData();
  } catch (error) {
    setStatus('error', error.message);
  }
}

async function selectRestaurant(restaurantId, restaurantName) {
  if (!API_BASE) {
    alert('외부 API 서버가 연결되어 있지 않습니다.');
    return;
  }

  try {
    await apiCall(`/api/visit/${restaurantId}`, 'POST');
    setStatus('success', `${restaurantName} 방문 기록을 저장했습니다.`);
    await loadLiveData();
  } catch (error) {
    setStatus('error', error.message);
  }
}

async function initializePage() {
  if (API_BASE) {
    try {
      await loadLiveData();
      return;
    } catch (error) {
      console.error(error);
    }
  }

  loadSampleData();
}

initializePage();
