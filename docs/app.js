const API_BASE = (window.LUNCH_API_BASE || '').replace(/\/$/, '');

const sampleWeather = {
  category: 'hot',
  summary: '덥고 습함',
  temperature_c: 29,
  note: '실내 좌석과 가벼운 메뉴에 가점',
};

const sampleVisits = [
  { restaurant_name: '을지로국밥', visited_on: '2026-06-20', meal_type: '점심', visit_count: 2, total_visit_count: 3 },
  { restaurant_name: '을지로짬뽕', visited_on: '2026-06-18', meal_type: '점심', visit_count: 1, total_visit_count: 1 },
  { restaurant_name: '을지로제육식당', visited_on: '2026-06-16', meal_type: '점심', visit_count: 1, total_visit_count: 1 },
];

const sampleRestaurants = [
  { id: 1, name: '을지로국밥', category: '한식', distance_m: 250, road_address: '서울 중구 을지로 일대', source: 'sample', main_menu: '국밥', estimated_calories: 700 },
  { id: 2, name: '을지로제육식당', category: '한식', distance_m: 430, road_address: '서울 중구 을지로 일대', source: 'sample', main_menu: '제육볶음', estimated_calories: 820 },
  { id: 3, name: '을지로파스타', category: '양식', distance_m: 580, road_address: '서울 중구 을지로 일대', source: 'sample', main_menu: '크림 파스타', estimated_calories: 850 },
  { id: 4, name: '을지로짬뽕', category: '중식', distance_m: 640, road_address: '서울 중구 을지로 일대', source: 'sample', main_menu: '짬뽕', estimated_calories: 800 },
];

const sampleRecommendations = [
  { id: 1, name: '을지로국밥', category: '한식', distance_m: 250, score: 6.4, price_level: '보통', recommendation_type: '재방문 추천', reason: '더운 날씨를 고려했고, 가까우며 익숙한 식당입니다.', main_menu: '국밥', estimated_calories: 700 },
  { id: 2, name: '을지로제육식당', category: '한식', distance_m: 430, score: 5.8, price_level: '보통', recommendation_type: '재방문 추천', reason: '든든한 점심 메뉴이고 이동 부담이 적습니다.', main_menu: '제육볶음', estimated_calories: 820 },
  { id: 4, name: '을지로짬뽕', category: '중식', distance_m: 640, score: 5.3, price_level: '보통', recommendation_type: '재방문 추천', reason: '실내 선호와 메뉴 다양성을 함께 반영했습니다.', main_menu: '짬뽕', estimated_calories: 800 },
  { id: 3, name: '을지로파스타', category: '양식', distance_m: 580, score: 4.9, price_level: '약간높음', recommendation_type: '새로운 도전', reason: '아직 방문 이력이 없는 신규 후보입니다.', main_menu: '크림 파스타', estimated_calories: 850 },
];

const state = {
  liveMode: Boolean(API_BASE),
};

async function apiCall(endpoint, method = 'GET', payload = null) {
  if (!API_BASE) {
    throw new Error('API_BASE가 설정되지 않았습니다.');
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

function setWeatherBadge(message) {
  const node = document.getElementById('weather-content');
  const badge = document.createElement('div');
  badge.className = 'api-badge';
  badge.textContent = message;
  node.appendChild(badge);
}

function renderWeather(weather) {
  const iconMap = { rainy: '🌧️', clear: '🌤️', hot: '☀️', cold: '🥶', unknown: '🌥️' };
  document.getElementById('weather-content').innerHTML = `
    <div class="weather-row">
      <div class="weather-icon">${iconMap[weather.category] || '🌥️'}</div>
      <div>
        <strong>오늘 점심 날씨: ${weather.summary}</strong>
        <p>기온 ${weather.temperature_c}°C</p>
        <p>${weather.note}</p>
      </div>
    </div>
  `;
  setWeatherBadge(state.liveMode ? '실제 API 연결 중' : '샘플 데이터 표시 중');
}

function recommendationCard(item, enableVisitButton) {
  const calories = item.estimated_calories ? `${item.estimated_calories}kcal` : '추정 불가';
  const buttonHtml = enableVisitButton
    ? `<button class="action-button" onclick="recordTodayVisit(${item.id}, '${item.name.replaceAll("'", "\\'")}')">오늘 방문 기록</button>`
    : `<button class="action-button" disabled>API 연결 시 방문 기록 가능</button>`;

  return `
    <article class="card restaurant-card">
      <div class="pill">${item.recommendation_type}</div>
      <h3>${item.name}</h3>
      <dl class="meta-grid">
        <div><dt>카테고리</dt><dd>${item.category}</dd></div>
        <div><dt>거리</dt><dd>${item.distance_m}m</dd></div>
        <div><dt>점수</dt><dd>${item.score}</dd></div>
        <div><dt>예산</dt><dd>${item.price_level}</dd></div>
        <div><dt>메인 메뉴</dt><dd>${item.main_menu || '추정 불가'}</dd></div>
        <div><dt>칼로리</dt><dd>${calories}</dd></div>
      </dl>
      <p class="reason">${item.reason}</p>
      ${buttonHtml}
    </article>
  `;
}

function renderRecommendations(items, enableVisitButton) {
  document.getElementById('recommendations').innerHTML = items
    .map((item) => recommendationCard(item, enableVisitButton))
    .join('');
}

function renderVisits(visits) {
  document.getElementById('visits').innerHTML = visits
    .map(
      (visit) => `
        <div class="list-item">
          <strong>${visit.restaurant_name}</strong>
          <span>${visit.visited_on} · ${visit.meal_type} · 당일 ${visit.visit_count}회 · 누적 ${visit.total_visit_count}회</span>
        </div>
      `
    )
    .join('');
}

function renderRestaurants(restaurants) {
  document.getElementById('restaurants').innerHTML = restaurants
    .map(
      (restaurant) => `
        <div class="list-item">
          <strong>${restaurant.name}</strong>
          <span>${restaurant.category} · ${restaurant.distance_m}m · ${restaurant.road_address || restaurant.address || '-'}</span>
          <span>메인 메뉴: ${restaurant.main_menu || '추정 불가'} · ${restaurant.estimated_calories || 0}kcal</span>
          <span>source=${restaurant.source}</span>
        </div>
      `
    )
    .join('');
}

async function loadLiveData() {
  const [weather, recommendationsPayload, visitsPayload, restaurantsPayload] = await Promise.all([
    apiCall('/api/weather'),
    apiCall('/api/recommendations'),
    apiCall('/api/visits'),
    apiCall('/api/restaurants'),
  ]);

  renderWeather(weather);
  renderRecommendations(recommendationsPayload.recommendations || [], true);
  renderVisits(visitsPayload.visits || []);
  renderRestaurants(restaurantsPayload.restaurants || []);
}

function loadSampleData() {
  renderWeather(sampleWeather);
  renderRecommendations(sampleRecommendations, false);
  renderVisits(sampleVisits);
  renderRestaurants(sampleRestaurants);
}

async function recordTodayVisit(restaurantId, restaurantName) {
  if (!API_BASE) {
    alert('GitHub Pages만으로는 저장할 수 없습니다. 외부 API 서버를 연결해 주세요.');
    return;
  }

  try {
    await apiCall(`/api/visit/${restaurantId}`, 'POST');
    alert(`${restaurantName} 오늘 방문 횟수가 기록되었습니다.`);
    await loadLiveData();
  } catch (error) {
    alert(`방문 기록 저장 실패: ${error.message}`);
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

  state.liveMode = false;
  loadSampleData();
}

initializePage();
